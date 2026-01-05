from flask import Flask, render_template, request
from services.calculations import (
    calculate_household,
    calculate_public_transport,
    calculate_vehicles,
    get_impact_level
)
from db_config import get_connection

app = Flask(__name__)

# ---------------- HOME ----------------
@app.route('/')
def index():
    return render_template('index.html')


# ---------------- INDIVIDUAL PAGE ----------------
@app.route('/individual')
def individual():
    return render_template('individual.html')


# ---------------- HOUSEHOLD PAGE ----------------
@app.route('/household')
def household():
    return render_template('household.html')


# ---------------- ADMIN PAGE ----------------
@app.route('/admin')
def admin():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT apartment_factor,
               detached_factor,
               attached_factor,
               diet_factor,
               rail_factor,
               bus_factor,
               vehicle_factor
        FROM EMISSION_FACTORS
        WHERE id = 1
    """)

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        return "Emission factors not found in database"

    return render_template(
        'admin.html',
        apartment=float(row[0]),
        detached=float(row[1]),
        attached=float(row[2]),
        diet=float(row[3]),
        rail=float(row[4]),
        bus=float(row[5]),
        vehicle=float(row[6])
    )


# ---------------- UPDATE FACTORS ----------------
@app.route('/update_factors', methods=['POST'])
def update_factors():

    apartment = float(request.form['apartment_factor'])
    detached = float(request.form['detached_factor'])
    attached = float(request.form['attached_factor'])
    diet = float(request.form['diet_factor'])
    rail = float(request.form['rail_factor'])
    bus = float(request.form['bus_factor'])
    vehicle = float(request.form['vehicle_factor'])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE EMISSION_FACTORS
        SET apartment_factor = %s,
            detached_factor = %s,
            attached_factor = %s,
            diet_factor = %s,
            rail_factor = %s,
            bus_factor = %s,
            vehicle_factor = %s
        WHERE id = 1
    """, (
        apartment,
        detached,
        attached,
        diet,
        rail,
        bus,
        vehicle
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return "<h3>Factors updated successfully!</h3><a href='/admin'>Go Back</a>"


# ---------------- CALCULATE ----------------
@app.route('/calculate', methods=['POST'])
def calculate():

    # ----- FETCH FACTORS FROM DB -----
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT apartment_factor,
               detached_factor,
               attached_factor,
               diet_factor,
               rail_factor,
               bus_factor,
               vehicle_factor
        FROM EMISSION_FACTORS
        WHERE id = 1
    """)

    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        return "Emission factors not found in database"

    # Convert ALL DB values to float immediately
    apartment_f = float(row[0])
    detached_f  = float(row[1])
    attached_f  = float(row[2])
    diet_f      = float(row[3])
    rail_f      = float(row[4])
    bus_f       = float(row[5])
    vehicle_f   = float(row[6])

    # ----- MAP USER CHOICES -----
    HOUSE_TYPE_MAP = {
        "Apartment": apartment_f,
        "Detached": detached_f,
        "Attached": attached_f
    }

    DIET_MAP = {
        "Vegetarian": diet_f,
        "Omnivore": diet_f,
        "HeavyMeat": diet_f,
        "Vegan": diet_f,
        "NoBeef": diet_f
    }

    # -------- HOUSEHOLD --------
    house_type_key = request.form.get('house_type')
    house_factor = HOUSE_TYPE_MAP.get(house_type_key, apartment_f)

    house_size = float(request.form.get('house_size', 1))
    electricity = float(request.form.get('electricity', 1))
    residents = int(request.form.get('residents', 1))

    diet_key = request.form.get('diet')
    diet_factor = DIET_MAP.get(diet_key, diet_f)

    household_emission = calculate_household(
        house_factor,
        house_size,
        electricity,
        diet_factor,
        residents
    )

    # -------- TRANSPORT --------
    rail_above = float(request.form.get('rail_above', 0))
    rail_below = float(request.form.get('rail_below', 0))
    bus = float(request.form.get('bus', 0))

    transport_emission = calculate_public_transport(
        float(rail_above) * rail_f,
        float(rail_below) * rail_f,
        float(bus) * bus_f
    )

    # -------- VEHICLES --------
    vehicle_emission = 0
    vehicle_details = []

    if request.form.get('use_vehicle'):
        distances = request.form.getlist('distance[]')
        fuels = request.form.getlist('fuel[]')

        vehicle_emission, vehicle_details = calculate_vehicles(
            distances,
            fuels
        )

        vehicle_emission *= vehicle_f

    # -------- TOTAL --------
    total = round(
        household_emission +
        transport_emission +
        vehicle_emission,
        2
    )

    impact_level = get_impact_level(total)

    return render_template(
        'result.html',
        total=total,
        impact_level=impact_level,
        household_total=household_emission,
        transport_total=transport_emission,
        vehicle_total=vehicle_emission,
        vehicles=vehicle_details
    )


# ---------------- RUN ----------------
if __name__ == '__main__':
    app.run(debug=True)

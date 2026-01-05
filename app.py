from flask import Flask, render_template, request

from services.common import (
    calculate_public_transport,
    calculate_vehicles
)
from services.household_calculations import calculate_household
from services.individual_calculations import calculate_individual

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/household')
def household():
    return render_template('household.html')


@app.route('/individual')
def individual():
    return render_template('individual.html')

#admin page
@app.route('/admin')
def admin():
    from db_config import get_connection

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
    from db_config import get_connection

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



@app.route('/calculate', methods=['POST'])
def calculate():

    is_household = 'residents' in request.form

    # -------- HOME / LIVING --------
    if is_household:
        household_emission = calculate_household(
            request.form['house_type'],
            float(request.form['house_size']),
            float(request.form['electricity']),
            request.form['diet'],
            int(request.form['residents'])
        )
    else:
        household_emission = calculate_individual(
            request.form['house_type'],
            float(request.form['house_size']),
            float(request.form['electricity']),
            request.form['diet']
        )

    # -------- TRANSPORT --------
    transport_emission = calculate_public_transport(
        float(request.form.get('rail_above', 0)) +
        float(request.form.get('rail_below', 0)),
        float(request.form.get('bus', 0))
    )

    # -------- VEHICLES --------
    vehicle_emission = 0
    vehicle_details = []

    if request.form.get('use_vehicle'):
        vehicle_emission, vehicle_details = calculate_vehicles(
            request.form.getlist('distance[]'),
            request.form.getlist('fuel[]')
        )

    total = round(
        household_emission +
        transport_emission +
        vehicle_emission,
        2
    )

    impact_level = (
        "Low" if total < 3 else
        "Moderate" if total <= 6 else
        "High"
    )

    return render_template(
        'result.html',
        total=total,
        impact_level=impact_level,
        household_total=household_emission,
        transport_total=transport_emission,
        vehicle_total=vehicle_emission,
        vehicles=vehicle_details
    )


if __name__ == "__main__":
    app.run(debug=True)

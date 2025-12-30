from db_config import get_connection


# -------------------------------------------------
# FETCH EMISSION FACTORS FROM MYSQL
# -------------------------------------------------
def get_emission_factors():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            apartment_factor,
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
        raise Exception("Emission factors row not found")

    return {
        "apartment": float(row[0]),
        "detached": float(row[1]),
        "attached": float(row[2]),
        "diet": float(row[3]),
        "rail": float(row[4]),
        "bus": float(row[5]),
        "vehicle": float(row[6])
    }


# -------------------------------------------------
# HOUSEHOLD CALCULATION
# -------------------------------------------------
def calculate_household(house_type, house_size, electricity, diet, residents):
    """
    Household emissions (tons CO2/year)
    """

    base_emission = (
        float(house_type) +
        float(house_size) +
        float(electricity)
    )

    household_emission = (base_emission * float(diet)) / max(int(residents), 1)

    return round(household_emission, 2)


# -------------------------------------------------
# INDIVIDUAL HOUSEHOLD (lighter version)
# -------------------------------------------------
def calculate_individual_household(house_type, house_size, electricity, diet):
    """
    Individual household footprint
    """
    base = float(house_type) + float(house_size) + float(electricity)
    return round(base * float(diet), 2)


# -------------------------------------------------
# PUBLIC TRANSPORT
# -------------------------------------------------
def calculate_public_transport(rail_above, rail_below, bus):
    """
    Weekly km → yearly emissions (tons CO2/year)
    """

    factors = get_emission_factors()

    rail_emission = (
        (float(rail_above) + float(rail_below))
        * factors["rail"]
        * 52
        / 1000
    )

    bus_emission = float(bus) * factors["bus"] * 52 / 1000

    total = rail_emission + bus_emission
    return round(total, 2)


# -------------------------------------------------
# MULTIPLE VEHICLE CALCULATION
# -------------------------------------------------
def calculate_vehicles(distances, fuels):
    """
    distance: km/year
    fuel: km/l
    """

    factors = get_emission_factors()

    vehicle_total = 0
    vehicle_details = []

    for i in range(len(distances)):
        distance = float(distances[i])
        fuel = float(fuels[i])

        if fuel > 0:
            emission = (distance / fuel) * factors["vehicle"] / 1000
        else:
            emission = 0

        emission = round(emission, 2)
        vehicle_total += emission

        vehicle_details.append({
            "vehicle_no": i + 1,
            "distance": distance,
            "fuel": fuel,
            "emission": emission
        })

    return round(vehicle_total, 2), vehicle_details


# -------------------------------------------------
# IMPACT LEVEL
# -------------------------------------------------
def get_impact_level(total):
    """
    Decide impact level based on total emission
    """
    if total < 2.5:
        return "Low"
    elif total <= 5:
        return "Moderate"
    else:
        return "High"

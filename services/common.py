from db_config import get_connection


def get_emission_factors():
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

    return {
        "Apartment": float(row[0]),
        "Detached": float(row[1]),
        "Attached": float(row[2]),
        "diet": float(row[3]),
        "rail": float(row[4]),
        "bus": float(row[5]),
        "vehicle": float(row[6])
    }


def calculate_public_transport(rail_km_week, bus_km_week):
    factors = get_emission_factors()

    rail_km_week = min(rail_km_week, 2000)
    bus_km_week = min(bus_km_week, 2000)

    rail_emission = rail_km_week * 52 * factors["rail"]
    bus_emission = bus_km_week * 52 * factors["bus"]

    return round(rail_emission + bus_emission, 2)


def calculate_vehicles(distances, fuels):
    factors = get_emission_factors()
    vehicle_factor = factors["vehicle"]

    total = 0
    details = []

    for i in range(len(distances)):
        distance = min(float(distances[i]), 100000)
        fuel = max(min(float(fuels[i]), 40), 5)

        emission = (distance / fuel) * vehicle_factor / 1000
        emission = round(emission, 2)
        total += emission

        details.append({
            "vehicle_no": i + 1,
            "distance": distance,
            "fuel": fuel,
            "emission": emission
        })

    return round(total, 2), details

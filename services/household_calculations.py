from services.common import get_emission_factors


def calculate_household(
    house_type,
    house_size,
    electricity,
    diet,
    residents
):
    """
    Per-person footprint in a household
    """

    factors = get_emission_factors()

    house_factor = factors.get(house_type, factors["Apartment"])

    # Electricity (monthly kWh → yearly CO2)
    electricity_emission = electricity * 12 * 0.00082

    # Housing baseline
    housing_emission = house_factor * house_size * 0.6

    # Diet impact
    diet_emission = factors["diet"]
    if diet == "HeavyMeat":
        diet_emission *= 1.2

    total = (electricity_emission + housing_emission + diet_emission) / max(residents, 1)

    return round(total, 2)

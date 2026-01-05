from services.common import get_emission_factors


def calculate_individual(
    house_type,
    house_size,
    electricity,
    diet
):
    """
    Total footprint of a single individual
    """

    factors = get_emission_factors()

    house_factor = factors.get(house_type, factors["Apartment"])

    electricity_emission = electricity * 12 * 0.00082
    housing_emission = house_factor * house_size * 0.6

    diet_emission = factors["diet"]
    if diet == "HeavyMeat":
        diet_emission *= 1.2

    total = electricity_emission + housing_emission + diet_emission
    return round(total, 2)

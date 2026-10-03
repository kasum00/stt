import requests


class WeatherProvider:

    BASE_URL = (
        "https://api.open-meteo.com/v1/forecast"
    )

    def get_weekly_forecast(
        self,
        latitude,
        longitude,
        days=7,
    ):

        params = {
            "latitude":
                latitude,

            "longitude":
                longitude,

            "daily": (
                "temperature_2m_mean,"
                "apparent_temperature_mean,"
                "precipitation_probability_max,"
                "precipitation_sum,"
                "weather_code"
            ),

            "timezone":
                "auto",

            "forecast_days":
                days,
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        daily = data[
            "daily"
        ]

        result = []

        for i in range(
            len(
                daily[
                    "time"
                ]
            )
        ):

            precipitation_probability = (
                daily[
                    "precipitation_probability_max"
                ][
                    i
                ]
            )

            precipitation_sum = (
                daily[
                    "precipitation_sum"
                ][
                    i
                ]
            )

            result.append(
                {
                    "date":
                        daily[
                            "time"
                        ][
                            i
                        ],

                    "temperature":
                        daily[
                            "temperature_2m_mean"
                        ][
                            i
                        ],

                    "apparent_temperature":
                        daily[
                            "apparent_temperature_mean"
                        ][
                            i
                        ],

                    "precipitation_probability":
                        precipitation_probability,

                    "precipitation_sum":
                        precipitation_sum,

                    "weather_code":
                        daily[
                            "weather_code"
                        ][
                            i
                        ],

                    "rain_risk":
                        (
                            (
                                precipitation_probability
                                is not None
                                and
                                precipitation_probability
                                >= 50
                            )
                            or
                            (
                                precipitation_sum
                                is not None
                                and
                                precipitation_sum
                                >= 1.0
                            )
                        ),
                }
            )

        return result
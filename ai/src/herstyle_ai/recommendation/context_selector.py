class ContextStructureSelector:

    def __init__(
        self,
        cold_threshold=20.0,
        hot_threshold=28.0,
    ):

        self.cold_threshold = float(
            cold_threshold
        )

        self.hot_threshold = float(
            hot_threshold
        )

    # =====================================================
    # SELECT STRUCTURE FROM CONTEXT
    # =====================================================

    def select(
        self,
        temperature,
        prefer_dress=False,
        context="office",
        raining=False,
    ):

        temperature = float(
            temperature
        )

        # =====================================
        # TEMPERATURE STATE
        # =====================================

        if temperature <= self.cold_threshold:

            temperature_state = "cool"

        elif temperature >= self.hot_threshold:

            temperature_state = "hot"

        else:

            temperature_state = "mild"

        # =====================================
        # DRESS PREFERENCE
        # =====================================

        if prefer_dress:

            if temperature_state == "cool":

                structure = (
                    "dress+outerwear+shoes"
                )

            else:

                structure = (
                    "dress+shoes"
                )

        # =====================================
        # NORMAL OFFICE OUTFIT
        # =====================================

        else:

            if temperature_state == "cool":

                structure = (
                    "top+bottom+outerwear+shoes"
                )

            else:

                structure = (
                    "top+bottom+shoes"
                )

        # =====================================
        # RESULT
        # =====================================

        return {

            "structure":
                structure,

            "decision_temperature":
                temperature,

            "temperature_state":
                temperature_state,

            "prefer_dress":
                bool(
                    prefer_dress
                ),

            "context":
                context,

            "raining":
                bool(
                    raining
                ),
        }
import numpy as np
import config


# ============================================================
# VIBRATION PROCESSOR
# ============================================================

class VibrationProcessor:

    def __init__(
        self,
        sample_rate=None
    ):

        if sample_rate is None:

            sample_rate = (
                config.ESP32_SAMPLE_RATE_HZ
            )

        self.sample_rate = sample_rate


    # ========================================================
    # REMOVE DC / GRAVITY COMPONENT
    # ========================================================

    def remove_dc(self, signal):

        signal = np.asarray(
            signal,
            dtype=float
        )

        return (
            signal
            - np.mean(signal)
        )


    # ========================================================
    # RMS
    # ========================================================

    def calculate_rms(self, signal):

        signal = np.asarray(
            signal,
            dtype=float
        )

        return np.sqrt(
            np.mean(
                signal ** 2
            )
        )


    # ========================================================
    # PEAK
    # ========================================================

    def calculate_peak(self, signal):

        signal = np.asarray(
            signal,
            dtype=float
        )

        return np.max(
            np.abs(signal)
        )


    # ========================================================
    # FFT
    # ========================================================

    def calculate_fft(self, signal):

        signal = np.asarray(
            signal,
            dtype=float
        )

        number_of_samples = len(
            signal
        )

        window = np.hanning(
            number_of_samples
        )

        windowed_signal = (
            signal * window
        )

        fft_values = np.fft.rfft(
            windowed_signal
        )

        frequencies = np.fft.rfftfreq(
            number_of_samples,
            d=1.0 / self.sample_rate
        )

        magnitude = np.abs(
            fft_values
        )

        if len(magnitude) > 0:

            magnitude[0] = 0

        dominant_index = np.argmax(
            magnitude
        )

        dominant_frequency = (
            frequencies[dominant_index]
        )

        return (
            frequencies,
            magnitude,
            dominant_frequency
        )


    # ========================================================
    # CONDITION
    # ========================================================

    def classify_condition(self, rms):

        if (
            rms
            <
            config.RMS_WARNING_THRESHOLD
        ):

            return "NORMAL"

        elif (
            rms
            <
            config.RMS_DANGER_THRESHOLD
        ):

            return "WARNING"

        else:

            return "DANGER"


    # ========================================================
    # COMPLETE PROCESSING
    # ========================================================

    def process(
        self,
        x,
        y,
        z
    ):

        x = np.asarray(
            x,
            dtype=float
        )

        y = np.asarray(
            y,
            dtype=float
        )

        z = np.asarray(
            z,
            dtype=float
        )


        # ----------------------------------------------------
        # Remove DC / gravity
        # ----------------------------------------------------

        x_processed = (
            self.remove_dc(x)
        )

        y_processed = (
            self.remove_dc(y)
        )

        z_processed = (
            self.remove_dc(z)
        )


        # ----------------------------------------------------
        # Vibration magnitude
        # ----------------------------------------------------

        vibration_magnitude = np.sqrt(

            x_processed ** 2

            +

            y_processed ** 2

            +

            z_processed ** 2

        )


        # ----------------------------------------------------
        # RMS
        # ----------------------------------------------------

        rms = self.calculate_rms(
            vibration_magnitude
        )


        # ----------------------------------------------------
        # Peak
        # ----------------------------------------------------

        peak = self.calculate_peak(
            vibration_magnitude
        )


        # ----------------------------------------------------
        # FFT
        # ----------------------------------------------------

        (
            frequencies,
            fft_magnitude,
            dominant_frequency
        ) = self.calculate_fft(
            x_processed
        )


        # ----------------------------------------------------
        # Condition
        # ----------------------------------------------------

        condition = (
            self.classify_condition(
                rms
            )
        )


        # ----------------------------------------------------
        # Return
        # ----------------------------------------------------

        return {

            "rms":
                float(rms),

            "peak":
                float(peak),

            "dominant_frequency":
                float(dominant_frequency),

            "condition":
                condition,

            "frequencies":
                frequencies,

            "fft_magnitude":
                fft_magnitude,

            "vibration":
                vibration_magnitude

        }
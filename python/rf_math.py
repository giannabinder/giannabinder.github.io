import numpy as np

class RFMath:
    """
    Unified Vectorized RF & Microwave Library.
    Supports single-frequency calculations and N-point frequency sweeps.
    """

    @staticmethod
    def format_matrix(M, spaces=""):
        """Formats a complex matrix for printing (supports single frequency only)."""
        if M.ndim > 2:
            return "[Frequency Array Data - Use plotting for visualization]"
        rows = []
        for row in M:
            row_str = "  ".join(f"{val.real:.3f}{val.imag:+.3f}j" for val in row)
            rows.append(row_str)
        return f"\n{spaces}".join(rows)

    # --- ABCD Matrix Generators ---

    @staticmethod
    def abcd_TL(freq, length, Zo, er=1):
        """Transmission Line ABCD Matrix."""
        c = 3e8
        beta = (2 * np.pi * freq * np.sqrt(er)) / c
        BL = beta * length
        A, B, C, D = np.cos(BL), 1j*Zo*np.sin(BL), 1j*(1/Zo)*np.sin(BL), np.cos(BL)
        return RFMath._package(A, B, C, D)

    @staticmethod
    def abcd_Z(Z):
        """Series Impedance ABCD Matrix."""
        A, B, C, D = 1, Z, 0, 1
        return RFMath._package(A, B, C, D)

    @staticmethod
    def abcd_Y(Z_shunt):
        """Shunt Admittance ABCD Matrix."""
        A, B, C, D = 1, 0, 1/Z_shunt, 1
        return RFMath._package(A, B, C, D)

    @staticmethod
    def abcd_transformer(N, one=1):
        """Ideal Transformer ABCD Matrix."""
        ratio = N/one
        A, B, C, D = ratio, 0, 0, 1/ratio
        return RFMath._package(A, B, C, D)

    @staticmethod
    def abcd_Y_inverter(J):
        """J-Inverter ABCD Matrix."""
        A, B, C, D = 0, -1j/J, -1j*J, 0
        return RFMath._package(A, B, C, D)

    @staticmethod
    def abcd_Z_3(Z1, Z2, Z3):
        """Pi or Tee Network (3-Impedance) ABCD Matrix."""
        s11 = 1 + Z1/Z3
        s12 = Z1 + Z2 + (Z1 * Z2 / Z3)
        s21 = 1 / Z3
        s22 = 1 + Z2 / Z3
        return RFMath._package(s11, s12, s21, s22)

    # --- Conversions & Analysis ---

    @staticmethod
    def abcd_to_s(ABCD, Zo=50):
        """Converts ABCD Matrix to S-Parameters."""
        # Extract elements correctly regardless of dimensions
        A, B, C, D = ABCD[..., 0, 0], ABCD[..., 0, 1], ABCD[..., 1, 0], ABCD[..., 1, 1]
        denom = A + (B / Zo) + (C * Zo) + D
        s11 = (A + (B / Zo) - (C * Zo) - D) / denom
        s12 = 2 * (A * D - B * C) / denom
        s21 = 2 / denom
        s22 = (-A + (B / Zo) - (C * Zo) + D) / denom
        return np.moveaxis(np.array([[s11, s12], [s21, s22]]), [0, 1], [-2, -1])

    @staticmethod
    def s_to_a(S, Zo=50):
        """Converts S-Parameters to ABCD Matrix."""
        s11, s12, s21, s22 = S[..., 0, 0], S[..., 0, 1], S[..., 1, 0], S[..., 1, 1]
        denom = 2 * s21
        A = ((1 + s11) * (1 - s22) + s12 * s21) / denom
        B = Zo * ((1 + s11) * (1 + s22) - s12 * s21) / denom
        C = (1 / Zo) * ((1 - s11) * (1 - s22) - s12 * s21) / denom
        D = ((1 - s11) * (1 + s22) + s12 * s21) / denom
        return np.moveaxis(np.array([[A, B], [C, D]]), [0, 1], [-2, -1])

    @staticmethod
    def cascade(*networks):
        """Matrix multiplication for cascaded networks."""
        result = networks[0]
        for net in networks[1:]:
            result = np.matmul(result, net)
        return result

    @staticmethod
    def _package(A, B, C, D):
        """Internal helper to package elements into 2x2 or Nx2x2 arrays."""
        if np.isscalar(A):
            return np.array([[A, B], [C, D]], dtype=complex)
        # Vectorized packaging
        ones = np.ones_like(A)
        zeros = np.zeros_like(A)
        # Convert constants to arrays if necessary
        if np.isscalar(B): B = B * ones
        if np.isscalar(C): C = C * ones
        return np.array([[A, B], [C, D]]).transpose(2, 0, 1)
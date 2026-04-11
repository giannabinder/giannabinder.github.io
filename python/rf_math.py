import numpy as np

class RFNetworks:
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
        return RFNetworks._package(A, B, C, D)

    @staticmethod
    def abcd_Z(Z):
        """Series Impedance ABCD Matrix."""
        A, B, C, D = 1, Z, 0, 1
        return RFNetworks._package(A, B, C, D)

    @staticmethod
    def abcd_Y(Y_shunt):
        """Shunt Admittance ABCD Matrix."""
        A, B, C, D = 1, 0, Y_shunt, 1
        return RFNetworks._package(A, B, C, D)

    @staticmethod
    def abcd_transformer(N, one=1):
        """Ideal Transformer ABCD Matrix."""
        ratio = N/one
        A, B, C, D = ratio, 0, 0, 1/ratio
        return RFNetworks._package(A, B, C, D)

    @staticmethod
    def abcd_Y_inverter(J):
        """J-Inverter ABCD Matrix."""
        A, B, C, D = 0, -1j/J, -1j*J, 0
        return RFNetworks._package(A, B, C, D)

    @staticmethod
    def abcd_Z_3(Z1, Z2, Z3):
        """Pi or Tee Network (3-Impedance) ABCD Matrix."""
        s11 = 1 + Z1/Z3
        s12 = Z1 + Z2 + (Z1 * Z2 / Z3)
        s21 = 1 / Z3
        s22 = 1 + Z2 / Z3
        return RFNetworks._package(s11, s12, s21, s22)

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
        # Broadcast to ensure all elements have the same shape (handles scalar A with array B/C)
        _A, _B, _C, _D = np.broadcast_arrays(A, B, C, D)
        if _A.ndim == 0:
            return np.array([[_A, _B], [_C, _D]], dtype=complex)
        
        # Stack and transpose to Nx2x2 format
        return np.array([[_A, _B], [_C, _D]], dtype=complex).transpose(2, 0, 1)

class RFMatching:
    """
    Module for Conjugate Matching, Maximum Gain, and Constant Gain Circles.
    Requires RFStability module for Delta calculations.
    """

    @staticmethod
    def conjugate_match(S):
        """
        Calculates Gamma_s and Gamma_l for maximum gain (conjugate match).
        Automatically selects the root with a magnitude < 1.
        """
        s11, s12, s21, s22 = S[..., 0, 0], S[..., 0, 1], S[..., 1, 0], S[..., 1, 1]
        delta = RFStability.get_delta(S)

        # Source Match (Gamma_s)
        B1 = 1 + np.abs(s11)**2 - np.abs(s22)**2 - np.abs(delta)**2
        C1 = s11 - delta * np.conj(s22)
        
        # Calculate both roots of the quadratic equation
        root_s = np.sqrt(B1**2 - 4 * np.abs(C1)**2 + 0j) # 0j ensures valid complex roots
        gamma_s_plus = (B1 + root_s) / (2 * C1)
        gamma_s_minus = (B1 - root_s) / (2 * C1)
        
        # Select the physically realizable root (|Gamma| < 1)
        gamma_s = np.where(np.abs(gamma_s_minus) < 1, gamma_s_minus, gamma_s_plus)

        # Load Match (Gamma_l)
        B2 = 1 + np.abs(s22)**2 - np.abs(s11)**2 - np.abs(delta)**2
        C2 = s22 - delta * np.conj(s11)
        
        root_l = np.sqrt(B2**2 - 4 * np.abs(C2)**2 + 0j)
        gamma_l_plus = (B2 + root_l) / (2 * C2)
        gamma_l_minus = (B2 - root_l) / (2 * C2)
        
        gamma_l = np.where(np.abs(gamma_l_minus) < 1, gamma_l_minus, gamma_l_plus)

        return gamma_s, gamma_l

    @staticmethod
    def max_gains(S):
        """
        Calculates maximum achievable gains: Transducer, Unilateral, Source, Load, and G0.
        Returns a dictionary containing linear and decibel values.
        """
        s11, s12, s21, s22 = S[..., 0, 0], S[..., 0, 1], S[..., 1, 0], S[..., 1, 1]
        gamma_s, gamma_l = RFMatching.conjugate_match(S)

        # Unilateral Gains
        GSmax = 1 / (1 - np.abs(s11)**2)
        GLmax = 1 / (1 - np.abs(s22)**2)
        G0max = np.abs(s21)**2
        GTUmax = GSmax * G0max * GLmax

        # Max Transducer Gain
        term1 = 1 / (1 - np.abs(gamma_s)**2)
        term2 = np.abs(s21)**2
        term3 = (1 - np.abs(gamma_l)**2) / (np.abs(1 - s22 * gamma_l)**2)
        GTmax = term1 * term2 * term3

        def to_db(linear_val): 
            return 10 * np.log10(linear_val)

        return {
            "GTmax": GTmax, "GTmax_dB": to_db(GTmax),
            "GTUmax": GTUmax, "GTUmax_dB": to_db(GTUmax),
            "GSmax": GSmax, "GSmax_dB": to_db(GSmax),
            "GLmax": GLmax, "GLmax_dB": to_db(GLmax),
            "G0max": G0max, "G0max_dB": to_db(G0max)
        }

    @staticmethod
    def constant_gain_source_circle(S, Gs_dB):
        """Calculates Center and Radius for Constant Gain Source Circle."""
        s11 = S[..., 0, 0]
        Gs_lin = 10**(Gs_dB / 10)
        GSmax = 1 / (1 - np.abs(s11)**2)
        gs = Gs_lin / GSmax

        denom = 1 - (1 - gs) * np.abs(s11)**2
        Cs_gain = (gs * np.conj(s11)) / denom
        Rs_gain = (np.sqrt(1 - gs) * (1 - np.abs(s11)**2)) / denom

        return Cs_gain, Rs_gain

    @staticmethod
    def constant_gain_load_circle(S, GL_dB):
        """Calculates Center and Radius for Constant Gain Load Circle."""
        s22 = S[..., 1, 1]
        GL_lin = 10**(GL_dB / 10)
        GLmax = 1 / (1 - np.abs(s22)**2)
        gl = GL_lin / GLmax

        denom = 1 - (1 - gl) * np.abs(s22)**2
        Cl_gain = (gl * np.conj(s22)) / denom
        Rl_gain = (np.sqrt(1 - gl) * (1 - np.abs(s22)**2)) / denom

        return Cl_gain, Rl_gain

    @staticmethod
    def unilateral_figure_of_merit(S):
        """
        Calculates U, lowerbound (dB), and upperbound (dB) for error bounds 
        when approximating bilateral devices as unilateral.
        """
        s11, s12, s21, s22 = S[..., 0, 0], S[..., 0, 1], S[..., 1, 0], S[..., 1, 1]
        
        # Implemented using the exact definition provided in your Desmos formulas
        numerator = np.abs(s12) * np.abs(s21) * np.abs(s11) * np.abs(s22)
        denominator = (1 - np.abs(s11)**2) * (1 - np.abs(s22)**2)
        U = numerator / denominator
        
        lowerbound_dB = -20 * np.log10(1 + U)
        upperbound_dB = -20 * np.log10(1 - U)
        
        return U, lowerbound_dB, upperbound_dB

    @staticmethod
    def single_stub_match(gamma_target, stub_type='open'):
        """
        Calculates series line length (d) and shunt stub length (l) in wavelengths.
        Matches a given gamma to the center of the Smith Chart (50 ohms).
        Returns both possible solutions (d1, l1) and (d2, l2).
        """
        rho = np.abs(gamma_target)
        theta = np.angle(gamma_target)
        
        # The 1+jb circle on the Gamma plane is (u - 0.5)^2 + v^2 = 0.25
        # Intersection with constant VSWR circle (u^2 + v^2 = rho^2) occurs at u = rho^2
        u_intersect = rho**2
        v_intersect = rho * np.sqrt(1 - rho**2)
        
        # Two intersection points on the 1+jb circle
        gamma_d1 = u_intersect + 1j * v_intersect
        gamma_d2 = u_intersect - 1j * v_intersect
        
        # Calculate distance 'd' towards generator (phase decreases by 2*beta*d)
        # 2*beta*d = angle(Gamma_L) - angle(Gamma_d) -> d = (angle_diff) / (4*pi)
        def calc_d(gamma_d):
            angle_diff = theta - np.angle(gamma_d)
            # Normalize to positive phase wrap
            if angle_diff < 0: angle_diff += 2 * np.pi
            return (angle_diff / (4 * np.pi)) % 0.5
            
        d1, d2 = calc_d(gamma_d1), calc_d(gamma_d2)
        
        # Calculate required stub susceptance (-b) to cancel the +jb of the line
        # y_d = (1 - gamma_d) / (1 + gamma_d) = 1 + jb
        y_d1 = (1 - gamma_d1) / (1 + gamma_d1)
        y_d2 = (1 - gamma_d2) / (1 + gamma_d2)
        b1, b2 = np.imag(y_d1), np.imag(y_d2)
        
        def calc_l(b):
            if stub_type == 'open':
                # y_stub = j*tan(beta*l) = -j*b  => tan(beta*l) = -b
                l = np.arctan(-b) / (2 * np.pi)
            else: # short
                # y_stub = -j*cot(beta*l) = -j*b => cot(beta*l) = b => tan(beta*l) = 1/b
                l = np.arctan(1/b) / (2 * np.pi)
            return l % 0.5
            
        return (d1, calc_l(b1)), (d2, calc_l(b2)), gamma_d1, gamma_d2

class RFStability:
    """
    Module for Stability Factor and Stability Circle Analysis.
    Integrates logic from Desmos for K-factor and Delta calculations.
    """

    @staticmethod
    def to_rect(mag, ang_deg):
        """Desmos: S(mag, ang) conversion helper."""
        return mag * np.exp(1j * np.radians(ang_deg))

    @staticmethod
    def get_delta(S):
        """Desmos: Δ = s11*s22 - s12*s21"""
        s11, s12, s21, s22 = S[..., 0, 0], S[..., 0, 1], S[..., 1, 0], S[..., 1, 1]
        return s11 * s22 - s12 * s21

    @staticmethod
    def get_k_factor(S):
        """Desmos: K = (1 - |s11|^2 - |s22|^2 + |Δ|^2) / (2 * |s12 * s21|)"""
        s11, s12, s21, s22 = S[..., 0, 0], S[..., 0, 1], S[..., 1, 0], S[..., 1, 1]
        delta = RFStability.get_delta(S)
        
        num = 1 - np.abs(s11)**2 - np.abs(s22)**2 + np.abs(delta)**2
        den = 2 * np.abs(s12 * s21)
        return num / den

    @staticmethod
    def source_stability_circle(S):
        """
        Calculates Center (Cs) and Radius (Rs) for the Source Stability Circle.
        Logic from Desmos 'Source Reflection Stability Circle' folder.
        """
        s11, s12, s21, s22 = S[..., 0, 0], S[..., 0, 1], S[..., 1, 0], S[..., 1, 1]
        delta = RFStability.get_delta(S)
        
        denom = np.abs(s11)**2 - np.abs(delta)**2
        Cs = np.conj(s11 - delta * np.conj(s22)) / denom
        Rs = np.abs(s12 * s21 / denom)
        return Cs, Rs

    @staticmethod
    def load_stability_circle(S):
        """
        Calculates Center (Cl) and Radius (Rl) for the Load Stability Circle.
        Logic from Desmos 'Load Reflection Stability Circle' folder.
        """
        s11, s12, s21, s22 = S[..., 0, 0], S[..., 0, 1], S[..., 1, 0], S[..., 1, 1]
        delta = RFStability.get_delta(S)
        
        denom = np.abs(s22)**2 - np.abs(delta)**2
        Cl = np.conj(s22 - delta * np.conj(s11)) / denom
        Rl = np.abs(s12 * s21 / denom)
        return Cl, Rl

class RFFilters:
    """
    Module for Filter Synthesis.
    Generates prototypes, lumped element values, and distributed network parameters.
    """

    @staticmethod
    def get_chebyshev_g_values(N, ripple_dB):
        """
        Calculates the low-pass prototype g-values for a Chebyshev filter
        for any order N and ripple (in dB). No lookup table required!
        """
        beta = np.log(1 / np.tanh(ripple_dB / 17.37))
        gamma = np.sinh(beta / (2 * N))
        
        a = [np.sin(((2 * k - 1) * np.pi) / (2 * N)) for k in range(1, N + 1)]
        b = [gamma**2 + np.sin((k * np.pi) / N)**2 for k in range(1, N + 1)]
        
        g = np.zeros(N + 2)
        g[0] = 1.0
        g[1] = (2 * a[0]) / gamma
        
        for k in range(2, N + 1):
            g[k] = (4 * a[k-2] * a[k-1]) / (b[k-2] * g[k-1])
            
        if N % 2 == 0:
            g[N+1] = 1.0 / (np.tanh(beta / 4)**2)
        else:
            g[N+1] = 1.0
            
        return g

    @staticmethod
    def design_lumped_bpf(N, ripple_dB, f0, fractional_bw, R0=50):
        """
        Q3.a) Computes the L and C values for a lumped-element Bandpass Filter.
        Automatically alternates between Series LC and Shunt LC branches.
        """
        g = RFFilters.get_chebyshev_g_values(N, ripple_dB)
        w0 = 2 * np.pi * f0
        T = fractional_bw
        
        components = {}
        components['R_source'] = g[0] * R0
        components['R_load'] = g[N+1] * R0 if N % 2 != 0 else (g[N+1] / R0)**-1

        for k in range(1, N + 1):
            if k % 2 != 0:
                # Odd k: Series LC branch
                Lk = (g[k] * R0) / (w0 * T)
                Ck = T / (w0 * g[k] * R0)
                components[f'L{k}_series'] = Lk
                components[f'C{k}_series'] = Ck
            else:
                # Even k: Shunt LC branch
                Lk = (T * R0) / (w0 * g[k])
                Ck = g[k] / (w0 * T * R0)
                components[f'L{k}_shunt'] = Lk
                components[f'C{k}_shunt'] = Ck
                
        return components

    @staticmethod
    def design_admittance_inverters(N, ripple_dB, fractional_bw, R0=50):
        """
        Computes Admittance Inverters, B values, and transmission line 
        lengths (theta/O and physical length L) for a distributed BPF.
        """
        g = RFFilters.get_chebyshev_g_values(N, ripple_dB)
        T = fractional_bw
        
        Z0J = np.zeros(N + 1)
        B = np.zeros(N + 1)
        Q = np.zeros(N + 1) 
        J = np.zeros(N + 1) # <--- Added J array
        
        for k in range(N + 1):
            if k == 0:
                Z0J[k] = np.sqrt((np.pi * T) / (2 * g[1]))
            elif k == N:
                Z0J[k] = np.sqrt((np.pi * T) / (2 * g[N] * g[N+1]))
            else:
                Z0J[k] = (np.pi * T) / (2 * np.sqrt(g[k] * g[k+1]))
            
            # Calculate J exactly as done in your Desmos
            J[k] = Z0J[k] / R0
            
            B[k] = (1 / R0) * (Z0J[k] / (1 - Z0J[k]**2))
            Q[k] = -np.arctan(2 * R0 * B[k])
            
        O = np.zeros(N)
        l = np.zeros(N)
        for k in range(N):
            O[k] = np.pi - 0.5 * (Q[k] + Q[k+1])
            l[k] = O[k] / (2 * np.pi)
            
        return {
            "Z0J": Z0J,
            "J_values": J, # <--- Now returning J
            "B": B,
            "Phi_rad": Q,
            "Theta_rad": O,
            "Lengths_wavelengths": l
        }
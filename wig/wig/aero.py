"""Item 3: aerodynamics in ground effect.

Method: steady vortex-ring lattice (Katz & Plotkin, "Low-Speed Aerodynamics", 2nd ed.,
sec. 12.3) with the ground represented by a mirror-image system (every ring mirrored at
z = 0 with circulation -Gamma, so the normal velocity vanishes on the water surface).
- Wing: rectangular planform, parabolic camber line, rotated about its trailing edge
  so that `h_te` is the trailing-edge height above the water.
- Endplates (the floats' inboard faces): thin vertical lifting surfaces hanging from the
  wing tips to depth min(endplate_depth, h_te - endplate_gap).
- Wake: straight, aligned with the free stream, 60 chords long, Kutta condition
  (wake ring Gamma = trailing-edge ring Gamma).
- Forces: Kutta-Joukowski on each ring's leading (bound) segment with net circulation
  (Gamma_ij - Gamma_(i-1)j).  Lift from the free stream; induced drag from the velocity
  induced by all streamwise segments (ring side legs + wakes + images) at the collocation
  point (K&P eq. 12.25-12.26).  This assumes full leading-edge suction, as all VLMs do; the
  fabric wing's real profile drag is a separate parameter (cd_profile_wing).
Limits: linear, inviscid, no stall.  Below h/c ~ 0.1 the real flow is nonlinear (ram
pressure, viscous channel) and the VLM underestimates lift growth.  Use the table for
h/c >= 0.1 with confidence, below that with a grain of salt.

Cross-checks included: Helmbold lift slope out of ground effect, McCormick induced-drag
factor phi = (16h/b)^2 / (1 + (16h/b)^2) in ground effect.
"""
import math
import numpy as np
from .params import Design, AIR

WAKE_LEN_CHORDS = 60.0


def _biot_savart(P, A, B, rel_core=1e-5):
    """Velocity at points P (n,3) induced by unit-strength segments A->B (m,3). Returns (n,m,3).
    K&P eq. 10.115.  A point closer to the segment's line than rel_core * segment length gets 0."""
    r1 = P[:, None, :] - A[None, :, :]
    r2 = P[:, None, :] - B[None, :, :]
    r0 = (B - A)[None, :, :]
    cr = np.cross(r1, r2)
    cr2 = np.einsum("ijk,ijk->ij", cr, cr)
    n1 = np.maximum(np.linalg.norm(r1, axis=2), 1e-12)
    n2 = np.maximum(np.linalg.norm(r2, axis=2), 1e-12)
    l0 = np.maximum(np.linalg.norm(r0, axis=2), 1e-12)
    dot = np.einsum("ijk,ijk->ij", r0, r1 / n1[..., None] - r2 / n2[..., None])
    core2 = (rel_core * l0) ** 2 * l0 ** 2          # |r1 x r2|^2 = (h |r0|)^2 with h = rel_core*|r0|
    coef = np.where(cr2 > core2, dot / (4 * math.pi * np.maximum(cr2, 1e-30)), 0.0)
    return cr * coef[..., None]


class Surface:
    """A lattice of vortex rings on a quadrilateral mesh of corner points pts[M+1, N+1, 3].

    i runs chordwise (0 = leading edge), j runs 'spanwise' (for the endplate: downward)."""
    def __init__(self, pts, name):
        self.name = name
        self.pts = pts
        M, N = pts.shape[0] - 1, pts.shape[1] - 1
        self.M, self.N = M, N
        # ring corners: panel corners shifted 1/4 panel-chord aft (K&P)
        dq = 0.25 * (pts[1:, :, :] - pts[:-1, :, :])
        ring = np.empty_like(pts)
        ring[:-1] = pts[:-1] + dq
        ring[-1] = pts[-1] + dq[-1]           # TE ring aft edge 1/4 panel behind TE
        self.ring = ring
        # collocation points at 3/4 panel chord, mid span; normals from panel diagonals
        c1 = pts[:-1, :-1]; c2 = pts[:-1, 1:]; c3 = pts[1:, 1:]; c4 = pts[1:, :-1]
        self.cp = 0.5 * ((c1 + c2) * 0.25 + (c4 + c3) * 0.75)
        nrm = np.cross(c3 - c1, c2 - c4)
        self.normal = nrm / np.linalg.norm(nrm, axis=2, keepdims=True)
        # panel 'span' vector of the leading (bound) segment of each ring
        self.bound_a = ring[:-1, :-1]; self.bound_b = ring[:-1, 1:]

    def ring_segments(self, i, j):
        r = self.ring
        p1, p2, p3, p4 = r[i, j], r[i, j + 1], r[i + 1, j + 1], r[i + 1, j]
        return [(p1, p2), (p2, p3), (p3, p4), (p4, p1)]


class VLM:
    def __init__(self, surfaces, V_inf=(1.0, 0.0, 0.0), ground=True, rho=AIR.rho, chord_ref=1.0):
        self._chord_ref = chord_ref
        self.surfaces = surfaces
        self.Vinf = np.array(V_inf, float)
        self.ground = ground
        self.rho = rho
        self._assemble()

    def _assemble(self):
        cps, nrms, bound_a, bound_b, owner = [], [], [], [], []
        segA, segB, segRing, segStream = [], [], [], []   # all segments, ring index, streamwise flag
        te_strips = []                                    # (ring, p_minus, p_plus, normal) for Trefftz
        ring_id = 0
        self.ring_index = []
        for s_id, s in enumerate(self.surfaces):
            idx = np.zeros((s.M, s.N), int)
            for i in range(s.M):
                for j in range(s.N):
                    cps.append(s.cp[i, j]); nrms.append(s.normal[i, j])
                    bound_a.append(s.bound_a[i, j]); bound_b.append(s.bound_b[i, j])
                    owner.append((s_id, i, j))
                    for k, (a, b) in enumerate(s.ring_segments(i, j)):
                        if i == s.M - 1 and k == 2:
                            continue    # TE ring's aft segment is cancelled by the wake ring (Kutta)
                        segA.append(a); segB.append(b); segRing.append(ring_id); segStream.append(k in (1, 3))
                    if i == s.M - 1:   # wake: two streamwise legs + far closing leg
                        p3 = s.ring[i + 1, j + 1]; p4 = s.ring[i + 1, j]
                        te_strips.append((ring_id, p4.copy(), p3.copy(), s.normal[i, j].copy()))
                        far = np.array([WAKE_LEN_CHORDS * self.chord_ref, 0, 0])
                        for (a, b) in [(p3, p3 + far), (p3 + far, p4 + far), (p4 + far, p4)]:
                            segA.append(a); segB.append(b); segRing.append(ring_id); segStream.append(True)
                    idx[i, j] = ring_id
                    ring_id += 1
            self.ring_index.append(idx)
        self.n = ring_id
        self.te_strips = te_strips
        self.cp = np.array(cps); self.normal = np.array(nrms)
        self.bound_a = np.array(bound_a); self.bound_b = np.array(bound_b)
        self.owner = owner
        A = np.array(segA); B = np.array(segB)
        ring = np.array(segRing); stream = np.array(segStream)
        if self.ground:
            Ai = A * np.array([1, 1, -1]); Bi = B * np.array([1, 1, -1])
            A = np.vstack([A, Ai]); B = np.vstack([B, Bi])
            sign = np.concatenate([np.ones(len(ring)), -np.ones(len(ring))])
            ring = np.concatenate([ring, ring]); stream = np.concatenate([stream, stream])
        else:
            sign = np.ones(len(ring))
        self.segA, self.segB, self.segRing, self.segStream, self.segSign = A, B, ring, stream, sign

    @property
    def chord_ref(self):
        return getattr(self, "_chord_ref", 1.0)

    def _influence(self, P, streamwise_only=False):
        """Velocity influence (n_points, n_rings, 3) per unit Gamma."""
        mask = self.segStream if streamwise_only else np.ones(len(self.segRing), bool)
        v = _biot_savart(P, self.segA[mask], self.segB[mask]) * self.segSign[mask][None, :, None]
        out = np.zeros((len(P), self.n, 3))
        np.add.at(out, (slice(None), self.segRing[mask]), v)
        return out

    def solve(self):
        AIC = np.einsum("ikc,ic->ik", self._influence(self.cp), self.normal)
        rhs = -self.normal @ self.Vinf
        self.gamma = np.linalg.solve(AIC, rhs)
        return self.gamma

    def induced_drag_trefftz(self):
        """Induced drag from the far wake (Trefftz plane).  Each trailing-edge strip sheds two
        semi-infinite lines carrying +/-Gamma_TE; far downstream they are 2-D point vortices
        (plus images with -Gamma at z -> -z).  D_i = -(rho/2) sum_j Gamma_j (v.n_j) l_j."""
        g = self.gamma
        ys, zs, gam = [], [], []
        for rid, pm, pp, n in self.te_strips:
            ys += [pp[1], pm[1]]; zs += [pp[2], pm[2]]; gam += [g[rid], -g[rid]]
        ys, zs, gam = np.array(ys), np.array(zs), np.array(gam)
        if self.ground:
            ys = np.concatenate([ys, ys]); zs = np.concatenate([zs, -zs]); gam = np.concatenate([gam, -gam])
        D = 0.0
        for rid, pm, pp, n in self.te_strips:
            mid = 0.5 * (pm + pp)
            dy = mid[1] - ys; dz = mid[2] - zs
            r2 = dy ** 2 + dz ** 2
            ok = r2 > 1e-10
            vy = np.sum(-gam[ok] * dz[ok] / (2 * math.pi * r2[ok]))
            vz = np.sum(gam[ok] * dy[ok] / (2 * math.pi * r2[ok]))
            l = np.linalg.norm(pp - pm)
            D += -0.5 * self.rho * g[rid] * (vy * n[1] + vz * n[2]) * l
        return D

    def forces(self, x_ref=0.0, z_ref=0.0):
        """Returns total force vector (N per unit rho? no: full N) and pitching moment about (x_ref, z_ref)."""
        g = self.gamma
        # net circulation on each ring's leading segment
        gnet = g.copy()
        for s_id, s in enumerate(self.surfaces):
            idx = self.ring_index[s_id]
            gnet[idx[1:, :].ravel()] = g[idx[1:, :].ravel()] - g[idx[:-1, :].ravel()]
        v_tr = np.einsum("ikc,k->ic", self._influence(self.cp, streamwise_only=True), g)
        l = self.bound_b - self.bound_a
        F = self.rho * gnet[:, None] * np.cross(self.Vinf[None, :] + v_tr, l)
        F_lift_only = self.rho * gnet[:, None] * np.cross(self.Vinf[None, :], l)
        mid = 0.5 * (self.bound_a + self.bound_b)
        # pitching moment (nose-up positive) about reference: M_y = (z - z_ref) * Fx - (x - x_ref) * Fz
        My = np.sum((mid[:, 2] - z_ref) * F[:, 0] - (mid[:, 0] - x_ref) * F[:, 2])
        return F.sum(axis=0), F_lift_only.sum(axis=0), My, F


def wing_mesh(d: Design, alpha_deg, h_te, M=8, N=24, camber=None):
    """Corner points of the wing lattice in wind axes (x downstream, z up, water at z=0)."""
    c, b = d.chord, d.span
    f = d.camber if camber is None else camber
    xs = 0.5 * (1 - np.cos(np.linspace(0, math.pi, M + 1)))            # cosine chordwise
    ys = -0.5 * np.cos(np.linspace(0, math.pi, N + 1))                    # cosine spanwise
    X, Y = np.meshgrid(xs * c, ys * b, indexing="ij")
    Z = 4 * f * c * (X / c) * (1 - X / c)
    a = math.radians(alpha_deg)
    # rotate about the trailing edge (x=c, z=0) by alpha nose-up; then lift so TE is at h_te
    xr = c + (X - c) * math.cos(a) + Z * math.sin(a)
    zr = -(X - c) * math.sin(a) + Z * math.cos(a) + h_te
    return np.stack([xr, Y, zr], axis=-1)


def endplate_mesh(wing_pts, side, depth, M, K=4):
    """Vertical plate hanging from the wing tip chord line (side=0 -> y=-b/2, side=-1 -> y=+b/2)."""
    tip = wing_pts[:, side, :]                       # (M+1, 3) tip chord line
    ks = np.linspace(0, 1, K + 1)
    pts = np.empty((M + 1, K + 1, 3))
    for i in range(M + 1):
        for kk, t in enumerate(ks):
            pts[i, kk] = tip[i] - np.array([0, 0, depth * t])
    if side == -1:     # keep ring orientation consistent (normal pointing outboard)
        pts = pts[:, ::-1, :]
    return pts


def solve_wing(d: Design, alpha_deg, h_te, endplates=True, ground=True, M=8, N=24, K=4,
               V=1.0, camber=None):
    """Lift, induced-drag and moment coefficients of the wing (+ endplates) in ground effect.

    h_te: trailing-edge height above water (m).  Coefficients referenced to wing area and chord;
    pitching moment about the wing quarter-chord at the height of the TE (nose-up positive)."""
    wing = wing_mesh(d, alpha_deg, h_te, M, N, camber)
    surfaces = [Surface(wing, "wing")]
    if endplates:
        depth = min(d.endplate_depth, max(h_te - d.endplate_gap, 0.0)) if ground else d.endplate_depth
        if depth > 0.01:
            surfaces.append(Surface(endplate_mesh(wing, 0, depth, M, K), "ep_L"))
            surfaces.append(Surface(endplate_mesh(wing, -1, depth, M, K), "ep_R"))
    vlm = VLM(surfaces, V_inf=(V, 0, 0), ground=ground, chord_ref=d.chord)
    vlm.solve()
    F, FL, My, _ = vlm.forces(x_ref=0.25 * d.chord, z_ref=h_te)
    Di = vlm.induced_drag_trefftz()
    q = 0.5 * AIR.rho * V ** 2
    S = d.wing_area
    return dict(CL=FL[2] / (q * S), CDi=Di / (q * S), Cm=My / (q * S * d.chord),
                CDi_nearfield=F[0] / (q * S), CL_total_force=F[2] / (q * S), n_panels=vlm.n)


# ---------------------------------------------------------------- empirical cross-checks
def helmbold_cla(AR):
    """Lift-curve slope (per rad) of a low-aspect-ratio wing OGE (Helmbold)."""
    return 2 * math.pi * AR / (2 + math.sqrt(AR ** 2 + 4))

def mccormick_phi(h, b):
    """Induced-drag ratio in ground effect, D_i(GE)/D_i(OGE) (McCormick 1979)."""
    x = 16 * h / b
    return x ** 2 / (1 + x ** 2)


# ---------------------------------------------------------------- lookup table for the sims
class GETable:
    """CL, CDi, Cm on an (alpha, h/c) grid with bilinear interpolation; stall clipped."""
    def __init__(self, d: Design, alphas=None, hcs=None, endplates=True, M=8, N=24, verbose=False):
        self.d = d
        self.alphas = np.array(alphas if alphas is not None else np.arange(-4, 16.1, 2.0))
        self.hcs = np.array(hcs if hcs is not None else [0.08, 0.12, 0.18, 0.25, 0.35, 0.5, 0.75, 1.0, 1.5, 3.0, 10.0])
        self.CL = np.zeros((len(self.alphas), len(self.hcs)))
        self.CDi = np.zeros_like(self.CL); self.Cm = np.zeros_like(self.CL)
        for j, hc in enumerate(self.hcs):
            for i, a in enumerate(self.alphas):
                r = solve_wing(d, a, hc * d.chord, endplates=endplates, M=M, N=N)
                self.CL[i, j], self.CDi[i, j], self.Cm[i, j] = r["CL"], r["CDi"], r["Cm"]
            if verbose:
                print(f"  h/c={hc:5.2f}: CL(8deg)={np.interp(8, self.alphas, self.CL[:, j]):.3f}")

    def _interp(self, tab, alpha, hc):
        from scipy.interpolate import RegularGridInterpolator
        f = RegularGridInterpolator((self.alphas, np.log(self.hcs)), tab, bounds_error=False, fill_value=None)
        a = np.clip(alpha, self.alphas[0], self.d.alpha_stall_deg)
        return float(f([[a, math.log(np.clip(hc, self.hcs[0], self.hcs[-1]))]])[0])

    def cl(self, alpha_deg, hc):  return self._interp(self.CL, alpha_deg, hc)
    def cdi(self, alpha_deg, hc): return self._interp(self.CDi, alpha_deg, hc)
    def cm(self, alpha_deg, hc):  return self._interp(self.Cm, alpha_deg, hc)

    def save(self, path):
        np.savez(path, alphas=self.alphas, hcs=self.hcs, CL=self.CL, CDi=self.CDi, Cm=self.Cm)

    @classmethod
    def load(cls, d, path):
        z = np.load(path)
        obj = cls.__new__(cls); obj.d = d
        obj.alphas, obj.hcs, obj.CL, obj.CDi, obj.Cm = z["alphas"], z["hcs"], z["CL"], z["CDi"], z["Cm"]
        return obj


# ---------------------------------------------------------------- whole-craft drag & PAR
def parasite_drag(V, d: Design, extra_cda=0.0):
    q = 0.5 * AIR.rho * V ** 2
    return q * (d.cda_parasite + d.cd_profile_wing * d.wing_area + extra_cda)


def slipstream_velocity(T, V, d: Design):
    """Fully developed slipstream velocity from actuator-disk theory."""
    return math.sqrt(max(V ** 2 + 2 * T / (AIR.rho * d.prop_area), 0.0))


def par_increment(T, V, cl, cdi, d: Design):
    """Power-augmented-ram lift/drag increments (blown-area model) and the thrust left for propulsion.

    Only valid if the prop is AHEAD of the wing and blows under it.  Captured fraction f of the
    slipstream raises dynamic pressure over the washed area S_j = min(1.1 D, b) * c; the captured
    jet is also turned down by par_turn_deg giving a reaction lift.  Optimistic placeholder: real
    PAR depends on trailing-edge sealing and endplate gaps (Gallington 1987).
    Returns (dL, dD, T_forward)."""
    if not d.par_enabled or T <= 0:
        return 0.0, 0.0, T
    f = d.par_capture
    Vj = slipstream_velocity(T, V, d)
    Sj = min(1.1 * d.prop_diam, d.span) * d.chord
    dq = 0.5 * AIR.rho * (Vj ** 2 - V ** 2)
    th = math.radians(d.par_turn_deg)
    dL = f * (dq * Sj * cl + T * math.sin(th))
    dD = f * dq * Sj * cdi
    T_fwd = T * (1 - f) + f * T * math.cos(th)
    return dL, dD, T_fwd

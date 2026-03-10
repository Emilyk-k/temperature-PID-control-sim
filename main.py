from plotly.subplots import make_subplots
import plotly.graph_objects as go

def PID(u_1, e, e_1, e_2):
    u = u_1 + (kp + ki * Tp + kd / Tp) * e + (-kp - 2 * kd / Tp) * e_1 + kd / Tp * e_2
    return u


def heater(u):
    qu = eff * min(max(qu_min, u), qu_max)
    return qu


def measure(temp_1, qu):
    # Skruch, Paweł. "A thermal model of the building for the design of temperature control algorithms." Automatyka/Automatics 18.1 (2014): 10-11.
    # https://journals.bg.agh.edu.pl/AUTOMAT/2014.18.1/automat.2014.18.1.9.pdf
    qo = 4.0 * A_w * Uo * (temp_1 - temp_o) + A_f * Uf * (temp_1 - temp_f) + A_f * Uo * (temp_1 - temp_o)
    Qo.append(qo)
    temp = temp_1 + Tp / (c * d * V) * (qu - qo)
    return temp

def temp_change(temp_f, temp_o):
    temp_f = temp_f + temp_i
    temp_o = temp_o + temp_i
    return temp_f, temp_o


def calculate(temp_f, temp_o):
    for i in range(N):
        t.append(t[-1] + Tp)
        temp.append(measure(temp[-1], Qu[-1]))  # measurement
        err.append(setpoint - temp[-1])  # error calculation
        pid_u.append(PID(pid_u[-1], err[-1], err[-2], err[-3]))
        Qu.append(heater(pid_u[-1]))  # actuator output
        temp_f, temp_o = temp_change(temp_f, temp_o)
    return t, temp, err, pid_u, Qu, temp_f, temp_o


def plot():
    fig = make_subplots(
        rows=2, cols=2,
        specs=[[{"colspan": 2}, None],
               [{"colspan": 2}, None]],
        print_grid=True)

    fig.add_trace(go.Scatter(x=t, y=temp, name='Room Temperature', hovertemplate=
    'Temperature [°C]: %{y:.2f}' +
    '<br>Time [s]: %{x:.0f}<br>'), row=1, col=1)

    fig.add_trace(go.Scatter(x=t, y=setpoint_lst, name='Setpoint', hovertemplate=
    'Temperature [°C]: %{y:.2f}' +
    '<br>Time [s]: %{x:.0f}<br>'), row=1, col=1)

    fig.add_trace(go.Scatter(x=t, y=Qu, name='Delivered Heat', hovertemplate=
    'Qu [J]: %{y:.0f}' +
    '<br>Time [s]: %{x:.0f}<br>'), row=2, col=1)

    fig.add_trace(go.Scatter(x=t, y=Qo, name='Dissipated heat', hovertemplate=
    'Qo [J]: %{y:.0f}' +
    '<br>Time [s]: %{x:.0f}<br>'), row=2, col=1)

    xtickvals = [x for x in t if x % 300 == 0]
    xticktext = [x / 60 for x in xtickvals]

    # Update axis properties
    fig.update_layout(yaxis=dict(title_text="Temperature [°C]"),
                      yaxis2=dict(title_text="Heat [J]"),
                      xaxis=dict(tickmode='array', tickvals=xtickvals, ticktext=xticktext,
                                 title_text="Time [min]"),
                      xaxis2=dict(tickmode='array', tickvals=xtickvals, ticktext=xticktext,
                                  title_text="Time [min]"),
                      height=800,
                      width=1000
                      )

    fig.show()

if __name__ == '__main__':
    # initialize variables
    Tp = 1
    tsim = 3600.0  # simulation time [s]
    N = int(tsim / Tp) + 1
    t = [0.0]

    # house
    h = 2.5  # room height [m]
    l = 4.0  # room length or width [m]
    A_w = h * l  # wall area [m^2]
    A_f = l * l  # floor/ceiling area [m^2]
    c = 1210.0  # specific heat capacity of air [J/(m^3 * °C)]
    d = 1.1839  # density of air [kg/m^3]
    V = h ** 3  # volume of air [m^3]
    Uo = 0.3  # heat transfer coefficient for outer space [W/m^2]
    Uf = 0.3  # heat transfer coefficient for floor [W/m^2]
    temp = [10.0]  # initial temperature [°C]
    temp_o = 0.0  # starting outer temperature [°C]
    temp_f = 5.0  # starting floor temperature (should be a few Celsius higher during day, lower during night) [°C]
    temp_ch = -2.0  # temperature change in 1 hour [°C]
    temp_i = tsim / 3600.0 * temp_ch / (N - 1)  # temperature increment every 1 minute [°C]
    Qo = []  # dissipated heat [J]

    # heater
    P = 2000.0  # maximum power of heater [W]
    qu_min = 0.0  # minimum heat delivered by heater in 1s [J]
    qu_max = P  # maximum heat delivered by heater in 1s [J]
    eff = 0.95  # efficiency of heater
    Qu = [0.0]  # actuator output / delivered heat [J]

    # PID
    pid_u = [0.0]  # initial conditions for control algorithm
    kp = 1000.0  # proportional gain (500.0 suggested)
    ki = 0.35  # integral coefficient (0.23 suggested)
    kd = 0.0  # derivative coefficient (0.0 suggested)
    setpoint = 25.0
    setpoint_lst = [setpoint] * (N + 1)
    err = [0.0, 0.0]

    t, temp, err, pid_u, Qu, temp_f, temp_o = calculate(temp_f, temp_o)
    plot()

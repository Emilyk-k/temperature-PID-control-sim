import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from ipywidgets import interact, FloatSlider, IntSlider, Layout

PI = np.pi
T_sim = 18000
def aktualizuj(V_litry, P_max, T_zad, Kp, Ti):
    V = V_litry / 1000

    rezultaty = przeprowadz_symulacje(V, P_max, T_zad, Kp, Ti)

    fig = sp.make_subplots(rows=5, cols=1, subplot_titles=(
        "Zmiany temperatury wody w zbiorniku w czasie",
        "Zmiany mocy grzałki w czasie",
        "Sygnał sterujący przed i po ograniczeniu",
        "Zużycie wody w czasie",
        "Bilans temperatury",
    ))

    fig.add_trace(go.Scatter(x=rezultaty["Czas"], y=rezultaty["Temperatura (°C)"], name="Temperatura"), row=1, col=1)
    fig.add_trace(go.Scatter(x=[0, T_sim / 60], y=[T_zad, T_zad], mode="lines", name="Temperatura zadana", line=dict(dash="dash")), row=1, col=1)

    fig.add_trace(go.Scatter(x=rezultaty["Czas"], y=rezultaty["Moc (W)"], name="Moc"), row=2, col=1)

    fig.add_trace(go.Scatter(x=rezultaty["Czas"], y=rezultaty["Przepływ wody (l/min)"]*1000*60, name="Przepływ wody"), row=4, col=1)

    fig.add_trace(go.Scatter(x=rezultaty["Czas"], y=rezultaty["Sygnał sterujący u"], name="u (sterowanie)", line=dict(color='blue', dash='dash')), row=3, col=1)
    fig.add_trace(go.Scatter(x=rezultaty["Czas"], y=rezultaty["Sygnał sterujący u_n"], name="u_n (ograniczone)", line=dict(color='red')), row=3, col=1)

    fig.add_trace(go.Scatter(x=rezultaty["Czas"], y=rezultaty["Zysk temperatury"]*60, name="Zysk temperatury", line=dict(color='rgba(255, 0, 0, 0.5)')), row=5, col=1)
    fig.add_trace(go.Scatter(x=rezultaty["Czas"], y=rezultaty["Strata temperatury"]*60, name="Strata temperatury", line=dict(color='rgba(0, 0, 255, 0.5)')), row=5, col=1)
    fig.add_trace(go.Scatter(x=rezultaty["Czas"], y=rezultaty["Zmiana temperatury"]*60, name="Zmiana temperatury", line=dict(color='purple', dash='dash')), row=5, col=1)
    
    fig.update_xaxes(title_text="Czas (min)", row=1, col=1)
    fig.update_yaxes(title_text="Temperatura (°C)", row=1, col=1)

    fig.update_xaxes(title_text="Czas (min)", row=2, col=1)
    fig.update_yaxes(title_text="Moc (W)", row=2, col=1)

    fig.update_xaxes(title_text="Czas (min)", row=4, col=1)
    fig.update_yaxes(title_text="Przepływ wody (l/min)", row=4, col=1)

    fig.update_xaxes(title_text="Czas (min)", row=3, col=1)
    fig.update_yaxes(title_text="Sygnał sterujący", row=3, col=1)

    fig.update_xaxes(title_text="Czas (min)", row=5, col=1)
    fig.update_yaxes(title_text="Zmiany temperatury(°C/min)", row=5, col=1)

    fig.update_layout(height=1200, title_text="Symulacja grzałki do wody", showlegend=True)
    return fig

def przeprowadz_symulacje(V, P_max, T_zad, Kp, Ti):
    R = 0.5
    srednica = 0.5
    cp = 4185  # J / kg / K 
    rho = 988  # kg / m^3
    tempo_przeplywu = 5 / 1000 / 60  # litr/min

    T_in = 15.0
    T_otoczenia = 20.0 
    Tp = 1
    dt = Tp
    N = int(T_sim / dt) + 1
    
    dlugosc = V / (PI * (srednica / 2) ** 2)
    powierzchnia = 2 * PI * (srednica / 2) * dlugosc + 2 * PI * (srednica / 2) ** 2

    okresy_korzystania = pd.read_csv("scenariusz.csv").values.tolist()

    T = [T_in]
    P = [0]
    Q = [0]
    Czas = [0]
    straty_ciepla = [0]
    u=[0]
    u_n=[0]
    temp_plus = [0]
    temp_minus = [0]
    dT = [0]
    u_max = 1
    u_min = 0
    P_min = 0;
    e = [0]


    for i in range(1, N):
        Czas.append(i * dt)

        e.append(T_zad - T[-1])

        u.append(Kp * e[-1])
        #u.append(Kp * (e[-1] + (Tp / Ti) * sum(e)))
        u_n.append(min(u_max,max(u_min,u[-1])))

        P_out = ((P_max - P_min)/(u_max-u_min)*(u_n[-1]-u_min) + P_min)
        P.append(P_out)

        uzywa_wody = any(poczatek <= i < koniec for poczatek, koniec in okresy_korzystania)
        if uzywa_wody:
            Q.append(tempo_przeplywu)
        else:
            Q.append(0)

        straty_ciepla.append(powierzchnia * (T[-1] - T_otoczenia) / R)
        
        temp_plus.append(P[-1] / (rho * cp * V) * dt) 
        temp_minus.append(-(Q[-1] * (T[-1] - T_in) / V + straty_ciepla[-1] / (rho * cp) * dt)) 
        
        dT.append(temp_plus[-1] + temp_minus[-1])

        T.append(max(min(T[-1] + dT[-1], 100), 0))

    rezultaty = pd.DataFrame({
        "Czas": np.array(Czas) / 60,
        "Temperatura (°C)": T,
        "Moc (W)": P,
        "Sygnał sterujący u": u,
        "Sygnał sterujący u_n": u_n,
        "Przepływ wody (l/min)": Q,
        "Zysk temperatury": temp_plus,
        "Strata temperatury": temp_minus,
        "Zmiana temperatury": dT,
    })

    return rezultaty

@interact(
    V_litry=IntSlider(
        value=80,
        min=50,
        max=200,
        step=5,
        description="Objętość zbiornika (litry)",
        layout=Layout(width='1000px'),
        style={'description_width': '200px'},
    ),
    P_max=IntSlider(
        value=2000,
        min=100,
        max=20000,
        step=100,
        description="Maksymalna moc grzałki (W)",
        layout=Layout(width='1000px'),
        style={'description_width': '200px'},
    ),
    T_zad=IntSlider(
        value=65.0,
        min=50.0,
        max=90.0,
        step=5,
        description="Temperatura zadana (°C)",
        layout=Layout(width='1000px'),
        style={'description_width': '200px'},
    ),
    Kp=FloatSlider(
        value=0.10,
        min=0.01,
        max=0.5,
        step=0.01,
        description="Kp",
        layout=Layout(width='1000px'),
        style={'description_width': '200px'},
    ),
        Ti=FloatSlider(
        value=100,
        min=100,
        max=100000,
        step=100,
        description="Ti",
        layout=Layout(width='1000px'),
        style={'description_width': '200px'},
    )
)
def symulacja_PI(V_litry=80, P_max=2000, T_zad=65, Kp=0.10, Ti = 100):
    fig = aktualizuj(V_litry, P_max, T_zad, Kp, Ti)
    fig.show()


import matplotlib.pyplot as plt
import pandas as pd

from cleaning import CLEAN_PATH, PROJECT_ROOT, run_cleaning


FIGURES_DIR = PROJECT_ROOT / "outputs" / "figures"


def save_bar_chart(data, title, filename, horizontal=False):
    """
    Recibe una Serie de pandas ya agrupada y guarda un grafico de barras.
    La uso para no repetir el mismo bloque de matplotlib en cada pregunta.
    """
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(10, 6))
    if horizontal:
        data.sort_values().plot(kind="barh", ax=ax, color="#2f6f73")
        ax.set_xlabel("Goles")
    else:
        data.plot(kind="bar", ax=ax, color="#2f6f73")
        ax.set_ylabel("Goles")
        ax.tick_params(axis="x", rotation=45)

    ax.set_title(title, fontsize=13, weight="bold")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / filename, dpi=160, bbox_inches="tight")
    plt.close(fig)


def result_state(team_goals, rival_goals):
    """
    Devuelve como estaba el partido desde el punto de vista del equipo de Messi.
    """
    if team_goals > rival_goals:
        return "Winning"
    if team_goals == rival_goals:
        return "Drawing"
    return "Losing"


def add_clutch_analysis(df):
    """
    Marca goles clutch.

    El CSV trae `score_at_goal`, que es el marcador despues del gol.
    Para reconstruir el marcador anterior resto 1 gol al equipo de Messi.

    Ejemplo:
    - Barcelona local, score_at_goal = 2:1
    - Antes del gol estaba 1:1
    - Paso de empate a victoria parcial, entonces es clutch.
    """
    df = df.copy()

    team_before = []
    rival_before = []
    state_before = []
    state_after = []

    for row in df.itertuples(index=False):
        left_score, right_score = row.score_at_goal.split(":")
        left_score = int(left_score)
        right_score = int(right_score)

        if row.venue == "Home":
            team_after_goal = left_score
            rival_after_goal = right_score
        else:
            team_after_goal = right_score
            rival_after_goal = left_score

        team_before_goal = team_after_goal - 1
        rival_before_goal = rival_after_goal

        team_before.append(team_before_goal)
        rival_before.append(rival_before_goal)
        state_before.append(result_state(team_before_goal, rival_before_goal))
        state_after.append(result_state(team_after_goal, rival_after_goal))

    df["team_goals_before"] = team_before
    df["rival_goals_before"] = rival_before
    df["result_before_goal"] = state_before
    df["result_after_goal"] = state_after

    df["is_equalizer"] = (df["result_before_goal"] == "Losing") & (df["result_after_goal"] == "Drawing")
    df["is_go_ahead_goal"] = (df["result_before_goal"] == "Drawing") & (df["result_after_goal"] == "Winning")
    df["is_clutch_goal"] = df["is_equalizer"] | df["is_go_ahead_goal"]
    return df


def run_analysis():
    """
    Ejecuta el EDA en el mismo orden que las preguntas del proyecto.

    No guarda tablas intermedias. Las tablas quedan en el diccionario `results`
    por si se quieren revisar desde Python, pero el unico output persistente
    son los graficos en `outputs/figures/`.
    """
    if not CLEAN_PATH.exists():
        run_cleaning()

    df = pd.read_csv(CLEAN_PATH, parse_dates=["date"])
    results = {}

    # a) Goles por anio: miro volumen anual y media movil para ver continuidad.
    goals_by_year = df.groupby("year").size().rename("goals").reset_index()
    goals_by_year["rolling_3y_avg"] = goals_by_year["goals"].rolling(3, min_periods=1).mean().round(2)
    results["goals_by_year"] = goals_by_year

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(goals_by_year["year"], goals_by_year["goals"], color="#2f6f73", label="Goles")
    ax.plot(
        goals_by_year["year"],
        goals_by_year["rolling_3y_avg"],
        color="#b23a48",
        marker="o",
        label="Media movil 3 anios",
    )
    ax.set_title("Goles por anio: volumen y continuidad", fontsize=13, weight="bold")
    ax.set_xlabel("Anio")
    ax.set_ylabel("Goles")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "goals_by_year.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    # b) Goles por competicion: cuento goles y guardo primera aparicion.
    goals_by_competition = (
        df.groupby("competition")
        .agg(goals=("competition", "size"), first_goal=("date", "min"), last_goal=("date", "max"))
        .sort_values(["goals", "first_goal"], ascending=[False, True])
        .reset_index()
    )
    results["goals_by_competition"] = goals_by_competition
    save_bar_chart(
        goals_by_competition.head(10).set_index("competition")["goals"],
        "Goles por competicion",
        "goals_by_competition.png",
        horizontal=True,
    )

    competition_timeline = (
        df.groupby("competition")
        .agg(first_goal=("date", "min"), goals=("competition", "size"))
        .sort_values("first_goal")
        .reset_index()
    )
    results["competition_timeline"] = competition_timeline

    # c) Local/visitante: comparo cantidad y porcentaje.
    goals_by_venue = df.groupby("venue").size().rename("goals").reset_index()
    goals_by_venue["share"] = (goals_by_venue["goals"] / goals_by_venue["goals"].sum() * 100).round(1)
    results["goals_by_venue"] = goals_by_venue
    save_bar_chart(goals_by_venue.set_index("venue")["goals"], "Goles local vs visitante", "goals_by_venue.png")

    # d) Rivales: cuento a que equipos les hizo mas goles.
    goals_by_opponent = (
        df.groupby("opponent")
        .agg(goals=("opponent", "size"), competitions=("competition", "nunique"))
        .sort_values("goals", ascending=False)
        .reset_index()
    )
    results["goals_by_opponent"] = goals_by_opponent
    save_bar_chart(
        goals_by_opponent.head(15).set_index("opponent")["goals"],
        "Rivales que mas sufrieron a Messi",
        "goals_by_opponent.png",
        horizontal=True,
    )

    # e) Recursos: uso `goal_type` para ver de que maneras convierte.
    goals_by_type = df.groupby("goal_type").size().rename("goals").sort_values(ascending=False).reset_index()
    goals_by_type["share"] = (goals_by_type["goals"] / goals_by_type["goals"].sum() * 100).round(1)
    results["goals_by_type"] = goals_by_type
    save_bar_chart(
        goals_by_type.head(10).set_index("goal_type")["goals"],
        "Recursos de gol",
        "goals_by_type.png",
        horizontal=True,
    )

    # f) Posicion: reviso desde que roles aparecen los goles.
    goals_by_position = (
        df.groupby("player_position").size().rename("goals").sort_values(ascending=False).reset_index()
    )
    goals_by_position["share"] = (goals_by_position["goals"] / goals_by_position["goals"].sum() * 100).round(1)
    results["goals_by_position"] = goals_by_position
    save_bar_chart(
        goals_by_position.set_index("player_position")["goals"],
        "Goles por posicion registrada",
        "goals_by_position.png",
    )

    # g) Edad: analizo si el volumen cae linealmente con los anios.
    goals_by_age = df.groupby("age").size().rename("goals").reset_index()
    results["goals_by_age"] = goals_by_age

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(goals_by_age["age"], goals_by_age["goals"], color="#1f2933", marker="o")
    ax.set_title("Goles por edad: longevidad productiva", fontsize=13, weight="bold")
    ax.set_xlabel("Edad")
    ax.set_ylabel("Goles")
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "goals_by_age.png", dpi=160, bbox_inches="tight")
    plt.close(fig)

    # h) Periodo del partido: divido los 90 minutos en 4 partes.
    period_order = ["1/4: 0-23", "2/4: 24-45", "3/4: 46-68", "4/4: 69-90+"]
    goals_by_period = df.groupby("minute_period").size().reindex(period_order).rename("goals").reset_index()
    goals_by_period["share"] = (goals_by_period["goals"] / goals_by_period["goals"].sum() * 100).round(1)
    results["goals_by_minute_period"] = goals_by_period
    save_bar_chart(
        goals_by_period.set_index("minute_period")["goals"],
        "Periodo del partido en que aparece",
        "goals_by_minute_period.png",
    )

    # i) Clutch: goles que empatan o ponen arriba a su equipo.
    df_with_clutch = add_clutch_analysis(df)
    clutch_goals = df_with_clutch[df_with_clutch["is_clutch_goal"]].copy()
    results["clutch_goals"] = clutch_goals

    return results


if __name__ == "__main__":
    run_analysis()
    print("Analisis terminado. Graficos guardados en outputs/figures/")

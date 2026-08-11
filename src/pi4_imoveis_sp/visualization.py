from plotly.graph_objects import Figure

PLOTLY_CHART_CONFIG = {
    "displayModeBar": False,
    "scrollZoom": False,
    "doubleClick": False,
}


def lock_chart_interactions(
    figure: Figure,
) -> Figure:
    figure.update_layout(
        dragmode=False,
        clickmode="none",
        hovermode="closest",
    )

    figure.update_xaxes(
        fixedrange=True,
    )

    figure.update_yaxes(
        fixedrange=True,
    )

    return figure

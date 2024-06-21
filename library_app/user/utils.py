import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from flask import current_app
from flask_login import current_user
from library_app.models import Section


def generate_plots():
    dicti = {section.title: 0 for section in Section.query.all()}
    for issuedbook in current_user.issuedbooks:
        dicti[issuedbook.book.section.title] += 1
    data = {"Section": list(dicti.keys()), "Frequency": list(dicti.values())}
    df = pd.DataFrame(data).sort_values(by="Frequency", ascending=False)
    threshold = 4
    if len(df) > threshold:
        other_freq = df["Frequency"][threshold:].sum()
        df = df.head(threshold)
        df.loc[len(df)] = ["Others", other_freq]
    plt.figure(figsize=(10, 6))
    bar_width = max(0.4, 1.6 / len(df))
    colors = plt.cm.tab20(np.arange(len(df)))
    plt.bar(df["Section"], df["Frequency"], color=colors, width=bar_width, alpha=0.8)
    plt.xlabel("Section")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45)
    plt.tight_layout()
    bar_chart_path = os.path.join(
        current_app.root_path,
        "static",
        "user/stats",
        f"{current_user.username}_bar_chart.png",
    )
    if os.path.exists(bar_chart_path):
        os.remove(bar_chart_path)
    plt.savefig(bar_chart_path)
    plt.figure(figsize=(7, 7))
    non_zero_sections = df[df["Frequency"] > 0]
    explode = [0.02] * len(non_zero_sections)
    plt.pie(
        non_zero_sections["Frequency"],
        labels=non_zero_sections["Section"],
        autopct="%1.1f%%",
        startangle=140,
        pctdistance=0.85,
        explode=explode,
        wedgeprops=dict(width=0.3),
    )
    plt.axis("equal")
    plt.tight_layout()
    plt.legend(title="Sections", loc="upper right")
    pie_chart_path = os.path.join(
        current_app.root_path,
        "static",
        "user/stats",
        f"{current_user.username}_pie_chart.png",
    )
    if os.path.exists(pie_chart_path):
        os.remove(pie_chart_path)
    plt.savefig(pie_chart_path)
"""Genere un rapport HTML autonome (index.html) a partir de l'analyse BottleNeck."""
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.utils

# ---------- Pipeline (identique au notebook) ----------
erp = pd.read_excel('data/erp.xlsx')
liaison = pd.read_excel('data/liaison.xlsx')
web = pd.read_excel('data/web.xlsx')

erp['stock_quantity_2'] = np.where(erp['stock_quantity'] < 0, 0, erp['stock_quantity'])
erp['stock_status'] = np.where(erp['stock_quantity_2'] > 0, 'instock', 'outofstock')
erp['onsale_web'] = np.where(erp['stock_status'] == 'outofstock', 0, erp['onsale_web'])
erp['price'] = erp['price'].abs()

coherents = erp[erp['price'] > erp['purchase_price']]
marge_moyenne = ((coherents['price'] - coherents['purchase_price']) / coherents['price']).mean()
erp['price_2'] = np.where(erp['price'] <= erp['purchase_price'],
                          round(erp['purchase_price'] / (1 - marge_moyenne), 2), erp['price'])

web_product = web[web['post_type'] == 'product']
web_f = web_product[['sku', 'post_title', 'total_sales', 'product_type']].dropna(subset=['sku'])

join = liaison.merge(erp, on='product_id', how='outer') \
              .merge(web_f, left_on='id_web', right_on='sku', how='left')
join['total_sales'] = join['total_sales'].fillna(0)
join['ca_par_article'] = join['total_sales'] * join['price_2']
join['valorisation_stock'] = join['stock_quantity_2'] * join['price_2']
join['rotation_stock'] = (join['stock_quantity_2'] / join['total_sales']).replace([np.inf, -np.inf], np.nan)
join['price_HT'] = join['price_2'] / 1.20
join['taux_marge'] = (join['price_HT'] - join['purchase_price']) / join['price_HT'] * 100

mean_p, std_p = join['price_2'].mean(), join['price_2'].std()
join['z_score'] = (join['price_2'] - mean_p) / std_p
join['outlier'] = np.where(join['z_score'].abs() > 3, 'Aberrant', 'Normal')

# ---------- KPIs ----------
ca_total = join['ca_par_article'].sum()
unites = join['total_sales'].sum()
val_stock = join['valorisation_stock'].sum()
stock_dormant = join[(join['stock_quantity_2'] > 0) & (join['total_sales'] == 0)]['valorisation_stock'].sum()
nb_outliers = (join['outlier'] == 'Aberrant').sum()
pareto = join.sort_values('total_sales', ascending=False).reset_index(drop=True)
pareto['cumul'] = pareto['total_sales'].cumsum() * 100 / pareto['total_sales'].sum()
pareto['rank'] = range(1, len(pareto) + 1)
nb_80 = (pareto['cumul'] <= 80).sum() + 1
pct_actif = nb_80 / (pareto['total_sales'] > 0).sum() * 100

# ---------- Figures ----------
figs = {}

top20 = join.sort_values('ca_par_article', ascending=False).head(20)
f = px.bar(top20, x='post_title', y='ca_par_article', text_auto='.0f',
           title="Top 20 des articles par chiffre d'affaires",
           labels={'post_title': '', 'ca_par_article': 'CA (€)'})
f.update_layout(template='plotly_white', height=450, showlegend=False)
f.update_xaxes(tickangle=-45)
f.update_traces(marker_color='#2E86C1', textposition='outside', cliponaxis=False)
figs['top20'] = f

f = px.line(pareto, x='rank', y='cumul', title='Courbe de Pareto — concentration des ventes',
            labels={'rank': 'Nombre de produits', 'cumul': '% cumulé des ventes'})
f.add_hline(y=80, line_dash='dash', line_color='#E67E22', annotation_text='80% des ventes')
f.add_vline(x=nb_80, line_dash='dash', line_color='#E74C3C',
            annotation_text=f'{nb_80} produits')
f.update_layout(template='plotly_white', height=400)
figs['pareto'] = f

f = px.histogram(join, x='price_2', color='outlier', nbins=50,
                 title='Répartition des prix — outliers (Z-score > 3)',
                 labels={'price_2': 'Prix (€)', 'outlier': 'Statut'},
                 color_discrete_map={'Normal': '#2ECC71', 'Aberrant': '#E74C3C'})
f.add_vline(x=mean_p, line_dash='dash', line_color='#2E86C1',
            annotation_text=f'Moyenne : {mean_p:.0f} €')
f.update_layout(template='plotly_white', height=400)
figs['prix'] = f

flop20 = join[join['rotation_stock'].notnull()].sort_values('rotation_stock', ascending=False).head(20)
f = px.bar(flop20, x='rotation_stock', y='post_title', orientation='h',
           title='Flop 20 — produits avec le plus de mois de stock',
           labels={'rotation_stock': 'Mois de stock', 'post_title': ''})
f.update_layout(template='plotly_white', height=550, yaxis=dict(autorange='reversed'))
f.update_traces(marker_color='#E67E22')
figs['flop20'] = f

corr = join[['stock_quantity_2', 'total_sales', 'price_HT']].corr().round(2)
f = px.imshow(corr, text_auto=True, color_continuous_scale='RdBu_r', zmin=-1, zmax=1,
              title='Corrélations — stock, ventes, prix',
              labels=dict(x='', y='', color='Corr.'))
f.update_layout(height=420)
figs['corr'] = f

plots = {k: f.to_json() for k, f in figs.items()}

# ---------- HTML ----------
fmt = lambda v: f"{v:,.0f}".replace(',', ' ')

html = f'''<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BottleNeck — Analyse stock &amp; ventes</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  :root {{ --blue:#2E86C1; --dark:#1B2A41; --grey:#5D6D7E; --bg:#F4F6F8; }}
  * {{ box-sizing:border-box; margin:0; }}
  body {{ font-family:'Segoe UI', system-ui, sans-serif; background:var(--bg); color:var(--dark); }}
  header {{ background:linear-gradient(135deg,#1B2A41,#2E86C1); color:#fff; padding:56px 24px 48px; text-align:center; }}
  header h1 {{ font-size:2rem; margin-bottom:10px; }}
  header p {{ opacity:.85; max-width:720px; margin:0 auto; line-height:1.5; }}
  .container {{ max-width:1080px; margin:0 auto; padding:32px 20px; }}
  .kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:16px; margin-top:-64px; margin-bottom:40px; }}
  .kpi {{ background:#fff; border-radius:12px; padding:20px; box-shadow:0 4px 14px rgba(0,0,0,.08); }}
  .kpi .v {{ font-size:1.6rem; font-weight:700; color:var(--blue); }}
  .kpi .l {{ font-size:.85rem; color:var(--grey); margin-top:4px; }}
  section {{ background:#fff; border-radius:12px; padding:28px; margin-bottom:28px; box-shadow:0 2px 8px rgba(0,0,0,.06); }}
  h2 {{ font-size:1.25rem; margin-bottom:6px; color:var(--dark); }}
  .sub {{ color:var(--grey); font-size:.9rem; margin-bottom:16px; }}
  .chart {{ width:100%; }}
  .reco li {{ margin:10px 0 10px 18px; line-height:1.55; }}
  .reco strong {{ color:var(--blue); }}
  .tag {{ display:inline-block; background:#EBF5FB; color:var(--blue); border-radius:20px;
          padding:5px 14px; font-size:.8rem; margin:3px; }}
  footer {{ text-align:center; color:var(--grey); font-size:.85rem; padding:24px; }}
  footer a {{ color:var(--blue); }}
  table {{ width:100%; border-collapse:collapse; font-size:.92rem; }}
  th,td {{ text-align:left; padding:10px 12px; border-bottom:1px solid #EAECEE; }}
  th {{ color:var(--grey); font-weight:600; }}
</style>
</head>
<body>
<header>
  <h1>BottleNeck — Optimisation de la gestion des données</h1>
  <p>Rapprochement et nettoyage de trois sources (ERP, liaison, WooCommerce) puis analyse
     du chiffre d'affaires, des stocks et des marges d'une boutique de vins &amp; spiritueux.</p>
</header>
<div class="container">

  <div class="kpis">
    <div class="kpi"><div class="v">{fmt(ca_total)} €</div><div class="l">Chiffre d'affaires</div></div>
    <div class="kpi"><div class="v">{unites:,.0f}</div><div class="l">Unités vendues</div></div>
    <div class="kpi"><div class="v">{fmt(val_stock)} €</div><div class="l">Valorisation du stock</div></div>
    <div class="kpi"><div class="v">{fmt(stock_dormant)} €</div><div class="l">Stock dormant (0 vente)</div></div>
  </div>

  <section>
    <h2>Chiffre d'affaires par article</h2>
    <p class="sub">Les 20 produits générant le plus de CA.</p>
    <div id="top20" class="chart"></div>
  </section>

  <section>
    <h2>Concentration des ventes (Pareto)</h2>
    <p class="sub">{nb_80} produits réalisent 80 % des ventes, soit {pct_actif:.0f} % du catalogue actif.
       Le CA repose sur un portefeuille large, sans dépendance à quelques best-sellers.</p>
    <div id="pareto" class="chart"></div>
  </section>

  <section>
    <h2>Distribution des prix</h2>
    <p class="sub">{nb_outliers} produits identifiés comme aberrants (Z-score &gt; 3) :
       des références premium qui tirent la moyenne vers le haut.</p>
    <div id="prix" class="chart"></div>
  </section>

  <section>
    <h2>Rotation des stocks</h2>
    <p class="sub">Mois de stock restant au rythme des ventes observées — les produits à déstocker en priorité.</p>
    <div id="flop20" class="chart"></div>
  </section>

  <section>
    <h2>Corrélations</h2>
    <p class="sub">Ventes/stock : +0,46 (les best-sellers sont réapprovisionnés) ·
       prix/ventes : −0,41 (les produits chers vendent moins en volume).</p>
    <div id="corr" class="chart"></div>
  </section>

  <section>
    <h2>Qualité des données — anomalies corrigées</h2>
    <table>
      <tr><th>Anomalie détectée</th><th>Volume</th><th>Correction</th></tr>
      <tr><td>Stock négatif</td><td>2 produits</td><td>Ramené à 0</td></tr>
      <tr><td>Statut de stock incohérent</td><td>2 produits</td><td>Recalculé selon la quantité</td></tr>
      <tr><td>Hors stock mais en vente en ligne</td><td>47 produits</td><td>Désactivés de la vente web</td></tr>
      <tr><td>Prix négatif</td><td>3 produits</td><td>Valeur absolue</td></tr>
      <tr><td>Vente à perte (prix &le; prix d'achat)</td><td>4 produits</td><td>Prix recalculé à la marge moyenne</td></tr>
      <tr><td>SKU manquants (non rapprochables)</td><td>2 lignes</td><td>Exclues de la jointure</td></tr>
    </table>
  </section>

  <section>
    <h2>Recommandations métier</h2>
    <ul class="reco">
      <li><strong>Déstockage ciblé</strong> : les produits du Flop 20 et le stock dormant
          (~{fmt(stock_dormant)} €) immobilisent de la trésorerie — promotions, bundles, mise en avant.</li>
      <li><strong>Fiabiliser le référentiel</strong> : corriger les prix et statuts à la source
          (ERP/WooCommerce) plutôt qu'en aval de l'analyse.</li>
      <li><strong>Piloter les références premium</strong> : surveiller la rotation des {nb_outliers}
          produits chers pour éviter le sur-stock.</li>
      <li><strong>Stabiliser les identifiants</strong> : les SKU spéciaux (bons cadeaux, variantes)
          appellent un identifiant unique stable entre ERP et site.</li>
    </ul>
  </section>

  <section>
    <h2>Méthodologie &amp; stack</h2>
    <p class="sub">Data cleaning · jointures multi-sources · statistiques descriptives ·
       détection d'outliers (Z-score) · indicateurs métier · data visualisation</p>
    <span class="tag">Python</span><span class="tag">pandas</span><span class="tag">numpy</span>
    <span class="tag">Plotly</span><span class="tag">Jupyter</span><span class="tag">Excel</span>
  </section>

</div>
<footer>
  Projet réalisé dans le cadre de la formation Data Analyst — OpenClassrooms ·
  <a href="https://github.com/nhat86/bottleneck-data-analysis">Code source sur GitHub</a>
</footer>

<script>
const plots = {json.dumps(plots)};
for (const [id, spec] of Object.entries(plots)) {{
  Plotly.newPlot(id, spec.data, spec.layout, {{responsive:true, displaylogo:false}});
}}
</script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as fp:
    fp.write(html)
print('index.html genere :', len(html), 'octets')

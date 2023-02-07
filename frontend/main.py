# ===============================================================================
# Copyright 2023 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
import io

from dash import Dash, Input, Output, html, dcc, State, ctx
from dash.dash_table import DataTable
import dash_bootstrap_components as dbc
import plotly.express as px
import requests
from PIL import Image
from numpy import array

dash_app = Dash(
    'tray_classifier',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Tray Classifier Tool",
    # background_callback_manager=background_callback_manager,
)

cols = [{'name': 'Label', 'id': 'label'},
        {'name': 'Count', 'id': 'count'}]
cols_scoreboard_table = [{'name': 'Name', 'id': 'name'},
                         {'name': 'TotalClassified', 'id': 'total'}]

baseurl = 'http://api:8000'

resp = requests.get(f'{baseurl}/users')
users = resp.json()


dash_app.layout = dbc.Container([dbc.Row(
    [html.H4('User', style={'display': 'inline-block', 'margin-right': 20}),
     dcc.Input(id='username', type='text', placeholder='',
               list='available_users',
               style={'display': 'inline-block'}),
     html.Datalist(
         id='available_users',
         children=[html.Option(value=word['name']) for word in users])
     ]),
    dbc.Row(dbc.ButtonGroup([dbc.Button('Next Image',
                                        id='next_image_btn'),
                             dbc.Button('Good',
                                        id='good_btn'),
                             dbc.Button('Bad',
                                        id='bad_btn'),
                             dbc.Button('Empty',
                                        id='empty_btn'),
                             dbc.Button('Multigrain',
                                        id='multigrain_btn'),
                             dbc.Button('Contaminant',
                                        id='contaminant_btn'),
                             dbc.Button('Blurry',
                                        id='blurry_btn'),
                             ])),
    dbc.Row([dbc.Col([html.Div(id='image_id',
                               style='display: none'),
                      html.Div(id='image_info'),
                      html.Div(id="image"), ]),
             dbc.Col([html.H2('Results'),
                      DataTable(columns=cols,
                                id='results_table'),
                      html.Div(id='results_info'),
                      html.H2('Scoreboard'),
                      DataTable(columns=cols_scoreboard_table,
                                id='scoreboard_table')
                      ]
                     )
             ]),
])


@dash_app.callback([Output('image', 'children'),
                    Output('image_id', 'children'),
                    Output('results_table', 'data'),
                    Output('results_info', 'children'),
                    Output('image_info', 'children'),
                    Output('scoreboard_table', 'data'),
                    ],
                   [Input('next_image_btn', 'n_clicks'),
                    Input('good_btn', 'n_clicks'),
                    Input('bad_btn', 'n_clicks'),
                    Input('empty_btn', 'n_clicks'),
                    Input('multigrain_btn', 'n_clicks'),
                    Input('contaminant_btn', 'n_clicks'),
                    Input('blurry_btn', 'n_clicks'),
                    State('image_id', 'children'),
                    State('username', 'value')],
                   )
def handle_image(n_clicks, good_n_clicks, bad_n_clicks, empty_n_clicks, multigrain_n_clicks,
                 contaminant_n_clicks, blurry_n_clicks, current_image_id, username):
    if ctx.triggered_id in ('good_btn', 'empty_btn',
                            'bad_btn', 'multigrain_btn',
                            'contaminant_btn', 'blurry_btn'):
        if current_image_id:
            label = ctx.triggered_id.split('_')[0]
            if username:
                requests.post(f'{baseurl}/label/{current_image_id}?label={label}&user={username}')
            else:
                requests.post(f'{baseurl}/label/{current_image_id}?label={label}')

    resp = requests.get(f'{baseurl}/results_report')
    report = resp.json()
    tabledata = report['table']

    url = f'{baseurl}/scoreboard'
    if username:
        url = f'{url}?user={username}'
    resp = requests.get(url)
    scoreboard_tabledata = resp.json()['table']

    results_info = f"Total={report['total']} Unclassified={report['unclassified']}"
    url = f'{baseurl}/unclassified_image_info'
    if current_image_id:
        url = f'{url}?image_id={current_image_id}'

    resp = requests.get(url)
    obj = resp.json()
    hid = obj['hashid']
    resp = requests.get(f'{baseurl}/unclassified_image?hashid={hid}')
    # print(resp, resp.text)
    img = Image.open(io.BytesIO(resp.content))
    fig = px.imshow(array(img),
                    # color_continuous_scale='gray'
                    )
    fig.update_layout(coloraxis_showscale=False,
                      # margin=dict(l=20, r=20, t=20, b=20),
                      height=800)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)

    image_info = f"{obj['name']}"
    return dcc.Graph(figure=fig), obj['id'], \
           tabledata, results_info, image_info, scoreboard_tabledata


app = dash_app.server
if __name__ == "__main__":
    dash_app.run_server(debug=True, port=8051)

# ============= EOF =============================================

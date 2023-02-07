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

dash_app.layout = dbc.Container([dbc.Row(dbc.ButtonGroup([dbc.Button('Next Image',
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
                                 dbc.Row(dbc.Col([html.Div(id='image_id',
                                                           style='display: none'),
                                                  html.Div(id="image"), ]))
                                 ])


@dash_app.callback([Output('image', 'children'),
                    Output('image_id', 'children')],
                   [Input('next_image_btn', 'n_clicks'),
                    Input('good_btn', 'n_clicks'),
                    Input('bad_btn', 'n_clicks'),
                    Input('empty_btn', 'n_clicks'),
                    Input('multigrain_btn', 'n_clicks'),
                    Input('contaminant_btn', 'n_clicks'),
                    Input('blurry_btn', 'n_clicks'),
                    State('image_id', 'children')],
                   )
def handle_image(n_clicks, good_n_clicks, bad_n_clicks, empty_n_clicks, multigrain_n_clicks,
                 contaminant_n_clicks, blurry_n_clicks, current_image_id):
    baseurl = 'http://api:8000'
    if ctx.triggered_id in ('good_btn', 'empty_btn',
                            'bad_btn', 'multigrain_btn',
                            'contaminant_btn', 'blurry_btn'):
        if current_image_id:
            label = ctx.triggered_id.split('_')[0]
            requests.post(f'{baseurl}/label/{current_image_id}?label={label}')


    # img = np.array(Image.open('img name.tiff'))
    print(current_image_id, 'asdf')
    url = f'{baseurl}/unclassified_image_info'
    if current_image_id:
        url = f'{url}?image_id={current_image_id}'

    resp = requests.get(url)
    obj = resp.json()
    hid = obj['hashid']
    resp = requests.get(f'{baseurl}/unclassified_image?hashid={hid}')
    # print(resp, resp.text)
    img = Image.open(io.BytesIO(resp.content))
    fig = px.imshow(array(img), color_continuous_scale='gray')
    fig.update_layout(coloraxis_showscale=False)
    fig.update_xaxes(showticklabels=False)
    fig.update_yaxes(showticklabels=False)
    fig.show()

    return dcc.Graph(figure=fig), obj['id']


app = dash_app.server
if __name__ == "__main__":
    dash_app.run_server(debug=True, port=8051)

# ============= EOF =============================================

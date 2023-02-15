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
import base64
import io
import pprint
import random

from dash import Dash, Input, Output, html, dcc, State, ctx
from dash.dash_table import DataTable
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import requests
from PIL import Image
from numpy import array, hstack, zeros, ones

dash_app = Dash(
    'tray_classifier',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Tray Classifier Tool",
    # background_callback_manager=background_callback_manager,
)

cols_count_table = [{'name': 'Label', 'id': 'label'},
                    {'name': 'Count', 'id': 'count'}]
cols_scoreboard_table = [{'name': 'Name', 'id': 'name'},
                         {'name': 'TotalClassified', 'id': 'total'}]
cols_image_table = [{'name': 'Name', 'id': 'name'},
                    {'name': 'Value', 'id': 'value'}]
baseurl = 'http://api:8000'

# LABELS = ('good', 'empty', 'multigrain', 'contaminant', 'blurry')
LABELS = ('good', 'empty', 'multigrain', 'contaminant')


def make_table(cols, tid):
    dt = DataTable(columns=cols,
                   style_data={"fontSize": "10px", "font-family": "verdana"},
                   style_header={"fontSize": "12px", "font-family": "verdana"},
                   id=tid)
    return dt


def make_example_col(label):
    if label == 'good':
        name = 'SingleGrain'
    else:
        name = label.capitalize()

    return dbc.Col([html.Div(id=f'{label}_graph'),
                    html.Div(dbc.Button(name,
                                        id=f'{label}_btn',
                                        style={'display': 'block',
                                               'margin-left': 'auto',
                                               'margin-right': 'auto'}
                                        ),
                             style={'display': 'block',
                                    'margin-top': '10px',
                                    'margin-bottom': '10px',
                                    }
                             ),
                    ],
                   width=3)


def make_example_row():
    cols = [make_example_col(label) for label in LABELS]
    return dbc.Row(cols, className='justify-content-center')


countbox_style = {'border': 'solid',
                  'border-radius': '10px',
                  }

dash_app.layout = html.Div(dbc.Container([
    dcc.ConfirmDialog(
        id='confirm-danger',
        message='Please enter a Username',
    ),
    dbc.Row(dbc.Col(html.H1('R-Hole'),
                    className='col-md-auto'),
            className='justify-content-center'),
    dbc.Row([dbc.Col(html.H3('Images')),
             dbc.Col(html.Div(html.H3(id='total_info', style={'color': 'green',
                                                              'margin': '5px'
                                                              })),
                     style=countbox_style),
             dbc.Col(html.Div(html.H3(id='unclassified_info', style={'color': 'orange',
                                                                     'margin': '5px'
                                                                     }),
                              style=countbox_style
                              ))]),
    dbc.Row(html.Div([html.H4('Username', style={'display': 'inline-block', 'margin-right': 20}),
                      dcc.Input(id='username', type='text', placeholder='',
                                list='available_users',
                                style={'display': 'inline-block', 'width': '20%'}),
                      html.Datalist(
                          id='available_users',
                          # children=[html.Option(value=word['name']) for word in users]
                      )
                      ])),
    # dbc.Row(dbc.ButtonGroup([dbc.Button('Next Image',
    #                                     id='next_image_btn'),
    #                          dbc.Button('SingleGrain',
    #                                     id='good_btn'),
    #                          dbc.Button('Bad',
    #                                     id='bad_btn'),
    #                          dbc.Button('Empty',
    #                                     id='empty_btn'),
    #                          dbc.Button('Multigrain',
    #                                     id='multigrain_btn'),
    #                          dbc.Button('Contaminant',
    #                                     id='contaminant_btn'),
    #                          dbc.Button('Blurry',
    #                                     id='blurry_btn'),
    #                          ])),
    make_example_row(),
    dbc.Row(dbc.Col(dbc.Button('Skip', id='skip_btn',
                               style={'margin-left': 'auto',
                                      'margin-right': 'auto',
                                      'margin-top': '10px',
                                      'margin-bottom': '10px',
                                      'display': 'block'}
                               ),
                    width=2),
            className='justify-content-center'),
    dbc.Row([dbc.Col([html.Div(id='image_id',
                               style='display: none'),
                      html.Div(id='label_guess',
                               style={'border-style': 'solid',
                                      'border-radius': '5px',
                                      'margin': '10px'
                                      }),
                      html.Div(id="image"), ]),
             dbc.Col([
                 dbc.Row([dbc.Col([html.H2('Image'),
                          make_table(cols_image_table,
                                     'image_table')]),
                          dbc.Col([html.H2('Results'),
                          make_table(cols_count_table,
                                     'results_table')])]),
                 html.H2('Leader Board'),
                 make_table(cols_scoreboard_table,
                            'scoreboard_table')])
             ])]),
    style={'backgroundColor': '#e3cc9e'}
)

graph_config = {'responsive': False, "displayModeBar": False, "displaylogo": False}


def make_example_graphs():
    url = f'{baseurl}/representative_images'
    resp = requests.get(url)
    images_obs = resp.json()

    imgs = []
    for l in LABELS:
        for i in images_obs:
            if i['label'] == l:
                buf = base64.b64decode(i['image'].encode())
                img = Image.open(io.BytesIO(buf))
                imgs.append(img)
                break
        else:
            imgs.append(None)

    gs = []
    for im in imgs:
        if im is None:
            im = zeros((150, 150, 3))

        fig = px.imshow(im)
        fig.update_layout(coloraxis_showscale=False,
                          paper_bgcolor='#e3cc9e',
                          margin=dict(l=0, r=0, t=0, b=0),
                          height=200)
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        fig.update_traces(hoverinfo='skip')
        g = dcc.Graph(figure=fig, config=graph_config)
        gs.append(g)
    # if ns:
    #     shape = (50, 50, 3)
    #     if imgs:
    #         for i in imgs:
    #             if i is not None:
    #                 shape = i.shape
    #                 break
    #
    #     nimgs = []
    #     z = zeros(shape)
    #     for i, l in enumerate(('good', 'bad', 'empty', 'multigrain', 'contaminant', 'blurry')):
    #         if l in ns:
    #             n = z
    #         else:
    #             n = imgs[i]
    #         nimgs.append(n)
    #     imgs = nimgs
    #
    # nimgs = []
    # for i in imgs[:-1]:
    #     h, w, d = i.shape
    #     pad = ones((h, 50, d)) * 255
    #     nimgs.append(hstack((i, pad)))
    #
    # nimgs.append(imgs[-1])
    # imgs = nimgs
    #
    # img = hstack(imgs)
    #
    # fig = px.imshow(img)

    return gs


def make_image_table(obj):
    data = []
    if obj:
        pprint.pprint(obj)
        data = [{'name': 'ID', 'value': obj['id']},
                {'name': 'Hash', 'value': obj['hashid'][:8]},
                {'name': 'Load', 'value': obj['loadname']},
                {'name': 'Tray', 'value': obj['trayname']},
                {'name': 'Hole', 'value': obj['hole_id']},
                ]

    return data


def make_label_guess(im):
    # class image using a prebuilt classifier
    return random.choice(LABELS)


@dash_app.callback([Output('image', 'children'),
                    Output('image_id', 'children'),
                    Output('results_table', 'data'),
                    Output('total_info', 'children'),
                    Output('unclassified_info', 'children'),
                    # Output('image_info', 'children'),
                    Output('scoreboard_table', 'data'),
                    Output('good_graph', 'children'),
                    Output('empty_graph', 'children'),
                    Output('multigrain_graph', 'children'),
                    Output('contaminant_graph', 'children'),
                    Output('image_table', 'data'),
                    Output('confirm-danger', 'displayed'),
                    Output('label_guess', 'children'),
                    Output('available_users', 'children')
                    ],
                   [
                       Input('good_btn', 'n_clicks'),
                       Input('skip_btn', 'n_clicks'),
                       Input('empty_btn', 'n_clicks'),
                       Input('multigrain_btn', 'n_clicks'),
                       Input('contaminant_btn', 'n_clicks'),
                       State('image_id', 'children'),
                       State('username', 'value'),
                       State('image', 'children'),
                       State('image_table', 'data'),
                   ],
                   )
def handle_image(good_n_clicks, skip_n_clicks, empty_n_clicks, multigrain_n_clicks,
                 contaminant_n_clicks, current_image_id, username,
                 efig, image_tabledata):
    display_confirm = False
    if ctx.triggered_id in ('good_btn', 'empty_btn',
                            'multigrain_btn',
                            'contaminant_btn', 'blurry_btn'):
        display_confirm = True
        if current_image_id:
            label = ctx.triggered_id.split('_')[0]
            if username:
                requests.post(f'{baseurl}/label/{current_image_id}?label={label}&user={username}')
                display_confirm = False

            # else:
            #     requests.post(f'{baseurl}/label/{current_image_id}?label={label}')

    resp = requests.get(f'{baseurl}/results_report')
    report = resp.json()
    tabledata = report['table']

    url = f'{baseurl}/scoreboard'
    if username:
        url = f'{url}?user={username}'
    resp = requests.get(url)
    scoreboard_tabledata = resp.json()['table']

    # results_info = f"Total= {report['total']} Unclassified= {report['unclassified']}"
    total_info = f"Total= {report['total']}"
    unclassified_info = f"Unclassified= {report['unclassified']}"

    obj = None
    if not display_confirm:
        url = f'{baseurl}/unclassified_image_info'
        if current_image_id:
            url = f'{url}?image_id={current_image_id}'

        resp = requests.get(url)
        obj = resp.json()

    graph = dcc.Graph(config=graph_config)
    # image_info = ''
    image_id = 0

    label_guess = '---'

    if obj:
        image_id = obj['id']
        hid = obj['hashid']
        resp = requests.get(f'{baseurl}/unclassified_image?hashid={hid}')
        # print(resp, resp.text)
        img = Image.open(io.BytesIO(resp.content))
        img = array(img)
        fig = px.imshow(img,
                        # color_continuous_scale='gray'
                        )

        fig.update_layout(coloraxis_showscale=False,
                          paper_bgcolor='#e3cc9e',
                          # margin=dict(l=20, r=20, t=20, b=20),
                          margin=dict(l=0, r=0, t=0, b=0),
                          height=480)
        fig.update_xaxes(showticklabels=False)
        fig.update_yaxes(showticklabels=False)
        graph.figure = fig
        image_table = make_image_table(obj)
        label_guess = make_label_guess(img)

    else:
        graph = efig
        image_table = image_tabledata

    label_guess = f"R-Hole's guess:  {label_guess}"
    good_graph, empty_graph, multigrain_graph, contaminant_graph = make_example_graphs()
    resp = requests.get(f'{baseurl}/users')
    users = resp.json()
    available_users = [html.Option(value=word['name']) for word in users]

    return graph, image_id, \
        tabledata, total_info, unclassified_info, scoreboard_tabledata, \
        good_graph, empty_graph, multigrain_graph, contaminant_graph, \
        image_table, display_confirm, label_guess, available_users


app = dash_app.server
if __name__ == "__main__":
    dash_app.run_server(debug=True, port=8051)

# ============= EOF =============================================

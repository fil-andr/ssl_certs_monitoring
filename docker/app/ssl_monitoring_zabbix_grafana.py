from pyzabbix.api import ZabbixAPI, ZabbixAPIException
import json
import os
import requests
from flask import request
from flask import Flask,render_template, request, flash
import urllib

grafana_apikey = os.environ['GRAFANA_APIKEY']
grafana_server = '192.168.1.61:3000'
dashboard_uid = 'yZYuxYIVz'
panel_file = f'{os.path.dirname(__file__)}/panel.json'

app = Flask(__name__,template_folder=r'/app/templates')

app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

def connect_to_zabbix_server():
    zabbix_server = 'http://192.168.1.10'
    zabbix_user = 'Admin'
    zabbix_passw = os.environ['ZABBIX_PASSWD']
    zapi = ZabbixAPI(url=zabbix_server, user=zabbix_user, password=zabbix_passw)
    return zapi

#####zabbix part
def zabbix_create_host(host, ssl_port, zab_obj):

    host_tamplate = {
        "host": host,
        "interfaces": [
            {
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": "127.0.0.1",
                "dns": "",
                "port": "10050"
            }
        ],
        "groups": [
            {
                "groupid": "2"
            }
        ],
        "templates": [
            {
                "templateid": "10273"
            }
        ],
        "macros": [
            {
                "macro": "{$HOST_NAME}",
                "value": host
            },
            {
                "macro": "{$PORT}",
                "value": ssl_port
            }
        ]
    }



    # create host
    zabbix_response = zab_obj.do_request(method="host.create",params=host_tamplate)

    # zabbix logout
    zab_obj.user.logout()
    return zabbix_response



###########grafana part
def get_dashboard_json():
    ### request to get dashboard json
    r = requests.get(f"http://{grafana_server}/api/dashboards/uid/{dashboard_uid}", headers={"Content-Type":"application/json", "Authorization":f"Bearer {grafana_apikey}"})
    return r.json()


### calculate new panel id
def panel_id_num(data):
    id_list = []
    for i in data["dashboard"]["panels"]:
        id_list.append(i["id"])
    return sorted(id_list)[len(id_list)-1] + 1



## construct new panel json
def new_panel(template_file, id_num, host):
    with open(template_file) as f:
        template_file = json.load(f)

    ## замена значений в шаблоне панели на переменные
    for i in template_file["targets"]:
        i.update({'host': {"filter": host}})

    template_file.update({"title": host})
    template_file.update({"id": id_num})
    return template_file


### post request to grafana API create new panel
def create_panel_in_dashboard(data):
    post_result = requests.post(f"http://{grafana_server}/api/dashboards/db",
                                headers={"Content-Type":"application/json", "Authorization":f"Bearer {grafana_apikey}"},
                                data=json.dumps(data))
    return post_result

#create_panel_in_dashboard()


@app.route('/ssl-certs-monitoring', methods=('GET', 'POST'))
def ssl_monitor():
    if request.method == 'POST':
        host = request.form['ip']
        ssl_port = request.form['port']
        if not host:
            flash('host is required!')
        elif not ssl_port:
            flash('port is required!')
        else: 
            ##coonect to zabbix server
            zab_obj = connect_to_zabbix_server()

            #### create host in zabbix
            try:
                zab_response = zabbix_create_host(host, ssl_port, zab_obj)
            except ZabbixAPIException as e:
                return str(e)

            ### get dashboard json
            data = get_dashboard_json()

            ### id для новой панели
            id_num = panel_id_num(data)

            ## modify panel template
            panel = new_panel(panel_file, id_num, host)

            ### add new pane to dashboard json
            data["dashboard"]["panels"].append(panel)

            ### post request to grafana API create new panel
            post_result = create_panel_in_dashboard(data)
            if post_result.status_code == 200:
                return f"host and panel for {host} successfully added to grafana status: {post_result.json()['status']},  zabbix response {zab_response}"
            else:
                return f"something wrong, status code {post_result.status_code}, zabbix response {post_result.json()}"

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8080)

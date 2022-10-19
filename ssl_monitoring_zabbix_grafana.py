from pyzabbix.api import ZabbixAPI
import sys
import os
import json
import requests

### check argument existance
if len(sys.argv) < 2:
    print(f'usage: {os.path.basename(__file__)} <ssl_hostname> <ssl_port>')
    sys.exit()

# scripts arguments
host = sys.argv[1]
ssl_port = sys.argv[2]



#####zabbix part
def zabbix_create_host(host_name):
    zabbix_server = 'http://192.168.1.10'
    zabbix_user = 'Admin'
    zabbix_passw = os.environ['ZABBIX_PASSWD']
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

    # Create ZabbixAPI class instance
    zapi = ZabbixAPI(url=f'{zabbix_server}/zabbix/', user=zabbix_user, password=zabbix_passw)

    # create host
    zapi.do_request(method="host.create",params=host_tamplate)

    # zabbix logout
    zapi.user.logout()

#### create host in zabbix
zabbix_create_host(host)

###########grafana part

grafana_apikey = os.environ['GRAFANA_APIKEY']
grafana_server = '192.168.1.61:3000'
dashboard_uid = 'yZYuxYIVz'

def get_dashboard_json():
    ### request to get dashboard json
    r = requests.get(f"http://{grafana_server}/api/dashboards/uid/{dashboard_uid}", headers={"Content-Type":"application/json", "Authorization":f"Bearer {grafana_apikey}"})
    return r.json()

### get dashboard json
data = get_dashboard_json()

##### открываем файл шаблона панели
#panel = data["dashboard"]["panels"][0]

### calculate new panel id
def panel_id_num():
    id_list = []
    for i in data["dashboard"]["panels"]:
        id_list.append(i["id"])
    return sorted(id_list)[len(id_list)-1] + 1

### id для новой панели
id_num = panel_id_num()

## construct new panel json


def new_panel(template_file):
    with open(template_file) as f:
        template_file = json.load(f)

    ## замена значений в шаблоне панели на переменные
    for i in template_file["targets"]:
        i.update({'host': {"filter": host}})

    template_file.update({"title": host})
    template_file.update({"id": id_num})
    return template_file

panel_file = 'E:\open instructions\script_garafana_api\panel.json'

panel = new_panel(panel_file)

### add new pane to dashboard json
data["dashboard"]["panels"].append(panel)

### post request to grafana API create new panel
def create_panel_in_dashboard():
    post_result = requests.post(f"http://{grafana_server}/api/dashboards/db",
                                headers={"Content-Type":"application/json", "Authorization":f"Bearer {grafana_apikey}"},
                                data=json.dumps(data))
    return post_result

create_panel_in_dashboard()


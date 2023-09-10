import requests
import json
import eaopack as eao
import numpy as np
import datetime as dt

# !!! remember to launch EAO server first!

#############################################################
### define test data   ######################################
#############################################################

node1 = eao.assets.Node('portf_node_1')
node2 = eao.assets.Node('portf_node_2')
timegrid = eao.assets.Timegrid(dt.date(2021,1,1), dt.date(2021,2,1), freq = 'd')
a1 = eao.assets.SimpleContract(name = 'SC_1', price = 'rand_price_1', nodes = node1 ,
                min_cap= -20., max_cap=20., start = dt.date(2021,1,10), end = dt.date(2021,1,20))
#a1.set_timegrid(timegrid)
a2 = eao.assets.SimpleContract(name = 'SC_2', price = 'rand_price_2', nodes = node1 ,
                min_cap= -5., max_cap=10.)#, extra_costs= 1.)
#a2.set_timegrid(timegrid)
a3 = eao.assets.SimpleContract(name = 'SC_3', price = 'rand_price_2', nodes = node2 ,
                min_cap= -1., max_cap=10., extra_costs= 1.)
a5 = eao.assets.Storage('storage', nodes = node1, \
     start=dt.date(2021,1,1), end=dt.date(2021,2,1),size=10, \
     cap_in=1.0/24.0, cap_out=1.0/24.0, start_level=5, end_level=5)
a6 = eao.assets.Transport(name = 'transport', nodes = [node1, node2])
#a3.set_timegrid(timegrid)
prices ={'rand_price_1': (np.random.rand(timegrid.T)-0.5),
        'rand_price_2': (5.*np.random.rand(timegrid.T)-0.5),
        }

portf = eao.portfolio.Portfolio([a1, a2, a3, a5, a6])
portf_draw  = eao.portfolio.Portfolio([a1, a2, a3, a5, a6])
op    = portf.setup_optim_problem(prices, timegrid)
res = op.optimize()

#############################################################
### basic interactions with server  #########################
#############################################################


#############################################################
# reset data stored
r = requests.get('http://127.0.0.1:5000/reset')
# read what data is available on server (keys only)
r = requests.get('http://127.0.0.1:5000/get_data_keys')

# read specific data set
r = requests.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
print('****nodes:')
for n in obj_std_nodes: print(n.name)
#############################################################


##################### manipulate list of std_nodes ##########
# nodes are specific objects
# to edit a portfolio we assign assets to nodes
# which defines the portfolio network

### add node to list of std_nodes
#    some very standard nodes are already there
#    nodes used in the portfolio are stored separately
new_node = eao.serialization.to_json(node1)
r = requests.put('http://127.0.0.1:5000/add_std_node', json = new_node)
# check and see if there
r = requests.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
print('****nodes now:')
for n in obj_std_nodes: print(n.name)

### delete node
# check
r = requests.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
print('****nodes:')
for n in obj_std_nodes: print(n.name)
#delete
del_node = 'node_power_2'
r = requests.put('http://127.0.0.1:5000/del_std_node', json = del_node)
# check
r = requests.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
print('****nodes now:')
for n in obj_std_nodes: print(n.name)

#############################################################
### feed data into server and run optimization  #############
#############################################################

#### reset data
r = requests.get('http://127.0.0.1:5000/reset')

#### set portfolio
s = eao.serialization.to_json(portf)
r = requests.put('http://127.0.0.1:5000/set_portf', json=s)

#### set timegrid
s = eao.serialization.to_json(timegrid)
r = requests.put('http://127.0.0.1:5000/set_timegrid', json=s)


#### set prices
## eao JSON version
s = eao.serialization.to_json(prices)
r = requests.put('http://127.0.0.1:5000/set_time_series_data', json=s)
## list version ... more likely to be used in other setups
## since we want to be independent of eao outside server
l = {}
for k in prices:
    l[k] = list(prices[k])
r = requests.put('http://127.0.0.1:5000/set_time_series_data', json=l)

#### do optimization
r = requests.get('http://127.0.0.1:5000/optimize')

#############################################################
### manipulate and understand assets & portfolio   ##########
#############################################################

################ understand objects
# understand EAO specific classes Unit, Node, Timegrid, StartEndValueDict, ...
# those objects may be e.g. Asset parameters
# ---> this allows to "browse" parameters for assets, portfolio, specific classes, etc
r = requests.put('http://127.0.0.1:5000/get_object_details', json = 'node')
print(r.text)
r = requests.put('http://127.0.0.1:5000/get_object_details', json = 'unit')
print(r.text)
r = requests.put('http://127.0.0.1:5000/get_object_details', json = 'StartEndValueDict')
print(r.text)
r = requests.put('http://127.0.0.1:5000/get_object_details', json = 'Storage')
print(r.text)
r = requests.put('http://127.0.0.1:5000/get_object_details', json = 'Asset')
print(r.text)
r = requests.put('http://127.0.0.1:5000/get_object_details', json = 'Portfolio')
print(r.text)

## in editing it will likely be useful to have an editor for
# Nodes -- with Units
# and StartEndValueDict
### separately

#################################################### manipulate portfolio

### delete an asset
# (1) assets in portf
r = requests.put('http://127.0.0.1:5000/get_data', json = 'portf_asset_names')
portf_asset_names = json.loads(r.text)
print(portf_asset_names)

# (2) delete an asset
r = requests.put('http://127.0.0.1:5000/portf_delete_asset', json = 'storage')
print(r.text)

# check
r = requests.put('http://127.0.0.1:5000/get_data', json = 'portf_asset_names')
portf_asset_names = json.loads(r.text)
print(portf_asset_names)

# (3) add asset
r = requests.put('http://127.0.0.1:5000/get_data', json = 'std_assets')
assets = json.loads(json.loads(r.text)) # as dict

## adding asset[1] from the standard assets
print('adding')
print(assets[1]['asset_type'])
print(assets[1]['name'])

r = requests.put('http://127.0.0.1:5000/portf_add_asset', json = json.dumps(assets[1]))

# check
r = requests.put('http://127.0.0.1:5000/get_data', json = 'portf_asset_names')
portf_asset_names = json.loads(r.text)
print(portf_asset_names)


################################################ manipulate assets
### get asset names
r = requests.put('http://127.0.0.1:5000/get_data', json = 'portf_asset_names')
asset_names = json.loads(r.text)

### get asset details - for asset name part of the portfolio (asset name, not class name)
r = requests.put('http://127.0.0.1:5000/get_asset_details', json='battery')
details = json.loads(r.text)
# keys
# * arguments --- argument types to define asset with 
# * parameters -- values
# ----> should help to build a GUI to manage asset parameters
#       attention with special parameters Node, Unit and StartEndValues
#       Those should be managed separately as available Nodes, Units, ... --> mostly from std_nodes etc
# * parameter_tree --- where to find and how to set - incl all parameters down th hierarchy
# * doc

print(details['parameters']['cap_in'])
print(details['arguments']['cap_in'])

### same works for the portfolio
r = requests.get('http://127.0.0.1:5000/get_portf_details')
details = json.loads(r.text)
# --- note: very simple arguments, only list of assets
#     but with assets very deep parameter tree, since asset parameters are inlcuded
print(details['arguments'])
print(details['parameter_tree'])
# Tree structure:  ['assets', 1, 'start'] -- points to the parameter start in asset 1

#########################################
####### set ALL parameters of an asset
# here the parameters of our storage asset
r = requests.put('http://127.0.0.1:5000/get_asset_details', json='battery')
params = json.loads(r.text)
params = params['parameters']
##### now change as you whish --- including asset type, since one parameter is the asset_type
##
#### change in asset and portf
# [asset name, parameter dict]
arg = ['battery', params]
r = requests.put('http://127.0.0.1:5000/set_all_asset_parameters', json=arg)

### check enhancement: assign nodes through stored list of nodes
# this allows us to assign nodes as node names to an asset. eao server then checks for 
# the right definition stored

################################## simplify node management
# (1) Nodes normally of type Node
type(a1.nodes[0])
print('old node: '+a1.nodes[0].name)
# (2) replace as example, manage nodes by names
a1.nodes[0] = 'node_power_2'
js = eao.serialization.to_json(a1)
r = requests.put('http://127.0.0.1:5000/set_nodes_from_list', json = js)
a1b = eao.serialization.load_from_json(r.text)
print('old node: '+a1b.nodes[0].name)


#########################################
####### set SINGLE parameters of an asset
# we are using the approach of accessing assets directly in the portfolio
# means also, we cannot alter std assets directly
### likely not necessary, since setting all parameters may be simpler

# our example is the battery
# let us get the battery details first
r = requests.put('http://127.0.0.1:5000/get_asset_details', json='battery')
details = json.loads(r.text)
# details['arguments'] shows us that there is a parameter
# cap_in_, which is of type float
# parameters shows it has the value 1
print(details['parameters']['cap_in'])
# details['doc'] tells us the meaning

# let us set it to 2 - 
# [asset name, parameter address, value
arg = ['battery', 'cap_in', 2]
r = requests.put('http://127.0.0.1:5000/set_asset_parameter', json=arg)

## check
r = requests.put('http://127.0.0.1:5000/get_asset_details', json='battery')
details = json.loads(r.text)
print(details['parameters']['cap_in'])

r = requests.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
print('****nodes now:')
for n in obj_std_nodes: print(n.name)


########   create network graph
### get encoded info on nodes and edges
r = requests.get('http://127.0.0.1:5000/get_network')
obj_net_data = json.loads(r.text)
print('network data on nodes & edges:')
print(r.text)

### show how to draw from the info
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

radius = 0.05

minx = 0
miny = 0
maxx = 0
maxy = 0

fig, ax = plt.subplots()
ax.set_aspect('equal')

### nodes
for k in obj_net_data['position']:
    circle = Circle(obj_net_data['position'][k], radius, color='yellow')
    maxx = max(maxx, obj_net_data['position'][k][0])
    maxy = max(maxy, obj_net_data['position'][k][1])
    minx = min(minx, obj_net_data['position'][k][0])
    miny = min(miny, obj_net_data['position'][k][1])    
    ax.add_patch(circle)
    plt.text(obj_net_data['position'][k][0], obj_net_data['position'][k][1], k)
### edges
# where assets are assigned to nodes UNdirected, no label
# where transport present, labeled and directed (!)
for link in obj_net_data['links']:
    if link['label'] == '':
        pos1 = obj_net_data['position'][link['source']]
        pos2 = obj_net_data['position'][link['target']]
        # plt.arrow(pos1[0], pos1[1], pos2[0]-pos1[0], pos2[1]-pos1[1] , shape = 'full', head_width = 0.0, )
        plt.plot([pos1[0], pos2[0]], [pos1[1], pos2[1]], 'r-')
    else:
        pos1 = obj_net_data['position'][link['source']]
        pos2 = obj_net_data['position'][link['target']]
        plt.arrow(pos1[0], pos1[1], pos2[0]-pos1[0], pos2[1]-pos1[1] , shape = 'right', head_width = 0.02, length_includes_head = True)
        plt.text(pos1[0]+.5*(pos2[0]-pos1[0]),pos1[1]+.5*(pos2[1]-pos1[1]), link['label'])

ax.set_xlim(minx-2*radius, maxx+2*radius)
ax.set_ylim(miny-2*radius, maxy+2*radius)
plt.axis('off')
plt.show()
pass

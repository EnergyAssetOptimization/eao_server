import flask_unittest

import json
import eaopack as eao
import numpy as np
import datetime as dt

from os.path import dirname, join
import sys
mypath = (dirname(__file__))
sys.path.append(join(mypath, '..'))

from eao_server import create_app

######################### dummy data ##################################################
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
                        cap_in=1.0/24.0, cap_out=1.0/24.0, start_level=5, end_level=5,
                        no_simult_in_out=True)
#a3.set_timegrid(timegrid)
prices ={'rand_price_1': (np.random.rand(timegrid.T)-0.5),
        'rand_price_2': (5.*np.random.rand(timegrid.T)-0.5),
        }

portf = eao.portfolio.Portfolio([a1, a2, a3, a5])
op = portf.setup_optim_problem(prices = prices, timegrid = timegrid)
res = op.optimize(solver = 'SCIP')
out = eao.io.extract_output(portf, op, res)
pass
###################################################################### end dummy data

class TestBasic(flask_unittest.ClientTestCase):
    # Assign the flask app object
    app = create_app()

    def test_basic_with_client(self, client):
        # Use the client here
        # Example request to a route returning "hello world" (on a hypothetical app)
        r = client.get('http://127.0.0.1:5000/reset')
        self.assertEqual(r._status_code, 200)
        r = client.get('http://127.0.0.1:5000/get_data_keys')
        self.assertEqual(r._status_code, 200)
        j = json.loads(r.text)
        assert 'std_nodes' in j
        assert 'std_assets' in j
        pass
    

    def test_get_network(self, client):
        ########   create network graph
        #### set portfolio
        s = eao.serialization.to_json(portf)
        r = client.put('http://127.0.0.1:5000/set_portf', json=s)
        ### get encoded info on nodes and edges
        
        r = client.get('http://127.0.0.1:5000/get_network')
        obj_net_data = json.loads(r.text)
        assert r.status_code == 200
        assert obj_net_data['nodes'][0]['id'] == 'portf_node_1'
        
    def test_run_through(self, client):
        #############################################################
        ### define test data   ######################################
        #############################################################

        # op    = portf.setup_optim_problem(prices, timegrid)
        # res = op.optimize()


        #############################################################
        r = client.get('http://127.0.0.1:5000/reset')
        assert r.status_code == 200

        ### read what data is available on server (keys only)
        r = client.get('http://127.0.0.1:5000/get_data_keys')
        assert r.status_code == 200

        ### read specific data set
        r = client.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
        assert r.status_code == 200
        obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
        print('****nodes:')
        for n in obj_std_nodes: print(n.name)
        #############################################################


        ##### manipulate list of std_nodes
        ### add node
        new_node = eao.serialization.to_json(node1)
        r = client.put('http://127.0.0.1:5000/add_std_node', json = new_node)
        assert r.status_code == 200
        ### check and see if there
        r = client.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
        assert r.status_code == 200
        obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
        print('****nodes now:')
        for n in obj_std_nodes: print(n.name)

        ### delete node
        # check
        r = client.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
        assert r.status_code == 200
        obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
        print('****nodes:')
        for n in obj_std_nodes: print(n.name)
        #delete
        del_node = 'node_power_2'
        r = client.put('http://127.0.0.1:5000/del_std_node', json = del_node)
        assert r.status_code == 200
        # check
        r = client.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
        assert r.status_code == 200
        obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
        print('****nodes now:')
        for n in obj_std_nodes: print(n.name)

        #############################################################
        ### feed data into server   #################################
        #############################################################

        #### reset data
        r = client.get('http://127.0.0.1:5000/reset')
        assert r.status_code == 200

        #### set portfolio
        s = eao.serialization.to_json(portf)
        r = client.put('http://127.0.0.1:5000/set_portf', json=s)
        assert r.status_code == 200

        #### set timegrid
        s = eao.serialization.to_json(timegrid)
        r = client.put('http://127.0.0.1:5000/set_timegrid', json=s)
        assert r.status_code == 200


        #### set prices
        ## eao JSON version
        s = eao.serialization.to_json(prices)
        r = client.put('http://127.0.0.1:5000/set_time_series_data', json=s)
        assert r.status_code == 200
        ## list version
        l = {}
        for k in prices:
                l[k] = list(prices[k])
        r = client.put('http://127.0.0.1:5000/set_time_series_data', json=l)

        #### do optimization
        r = client.get('http://127.0.0.1:5000/optimize')
        assert r.status_code == 200

        #### choose different solver & do optimization
        r = client.put('http://127.0.0.1:5000/set_solver', json = 'standard')
        assert r.status_code == 200        
        r = client.get('http://127.0.0.1:5000/optimize')
        assert r.status_code == 200
        r = client.put('http://127.0.0.1:5000/set_solver', json = 'ECOS')
        # r = client.put('http://127.0.0.1:5000/set_solver', json = 'SCIP') ### not installed, but likely standard choice

        assert r.status_code == 200        
        r = client.get('http://127.0.0.1:5000/optimize')
        assert r.status_code == 200

        #############################################################
        ### manipulate and understand assets & portfolio   ##########
        #############################################################

        ################ understand objects
        # understand EAO specific classes Unit, Node, Timegrid, StartEndValueDict, ...
        # those objects may be e.g. Asset parameters
        # ---> this allows to "browse" parameters for assets, portfolio, specific classes, etc
        r = client.put('http://127.0.0.1:5000/get_object_details', json = 'node')
        assert r.status_code == 200
        print(r.text)
        r = client.put('http://127.0.0.1:5000/get_object_details', json = 'unit')
        assert r.status_code == 200
        print(r.text)
        r = client.put('http://127.0.0.1:5000/get_object_details', json = 'StartEndValueDict')
        assert r.status_code == 200
        print(r.text)
        r = client.put('http://127.0.0.1:5000/get_object_details', json = 'Storage')
        assert r.status_code == 200
        print(r.text)
        r = client.put('http://127.0.0.1:5000/get_object_details', json = 'Asset')
        assert r.status_code == 200
        print(r.text)
        r = client.put('http://127.0.0.1:5000/get_object_details', json = 'Portfolio')
        assert r.status_code == 200
        print(r.text)

        ################### manipulate portfolio

        ### delete an asset
        # (1) assets in portf
        r = client.put('http://127.0.0.1:5000/get_data', json = 'portf_asset_names')
        assert r.status_code == 200
        portf_asset_names = json.loads(r.text)
        print(portf_asset_names)

        # (2) delete an asset
        r = client.put('http://127.0.0.1:5000/portf_delete_asset', json = 'storage')
        assert r.status_code == 200
        print(r.text)

        # check
        r = client.put('http://127.0.0.1:5000/get_data', json = 'portf_asset_names')
        assert r.status_code == 200
        portf_asset_names = json.loads(r.text)
        print(portf_asset_names)

        # (3) add asset
        r = client.put('http://127.0.0.1:5000/get_data', json = 'std_assets')
        assert r.status_code == 200
        assets = json.loads(json.loads(r.text)) # as dict

        ## adding asset[1] from the standard assets
        print('adding')
        print(assets[1]['asset_type'])
        print(assets[1]['name'])

        r = client.put('http://127.0.0.1:5000/portf_add_asset', json = json.dumps(assets[1]))
        assert r.status_code == 200

        # check
        r = client.put('http://127.0.0.1:5000/get_data', json = 'portf_asset_names')
        assert r.status_code == 200
        portf_asset_names = json.loads(r.text)
        print(portf_asset_names)


        ################ manipulate assets
        ### get asset names
        r = client.put('http://127.0.0.1:5000/get_data', json = 'portf_asset_names')
        assert r.status_code == 200
        asset_names = json.loads(r.text)

        ### get asset details - for asset name part of the portfolio (asset name, not class name)
        r = client.put('http://127.0.0.1:5000/get_asset_details', json='battery')
        assert r.status_code == 200
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
        r = client.get('http://127.0.0.1:5000/get_portf_details')
        assert r.status_code == 200
        details = json.loads(r.text)
        # --- note: very simple arguments, only list of assets
        #     but with assets very deep parameter tree, since asset parameters are inlcuded
        print(details['arguments'])
        print(details['parameter_tree'])
        # Tree structure:  ['assets', 1, 'start'] -- points to the parameter start in asset 1

        #########################################
        ####### set ALL parameters of an asset
        # here the parameters of our storage asset
        r = client.put('http://127.0.0.1:5000/get_asset_details', json='battery')
        assert r.status_code == 200
        params = json.loads(r.text)
        params = params['parameters']
        ##### now change as you whish --- including asset type, since one parameter is the asset_type
        ##
        #### change in asset and portf
        # [asset name, parameter dict]
        arg = ['battery', params]
        r = client.put('http://127.0.0.1:5000/set_all_asset_parameters', json=arg)
        assert r.status_code == 200

        ### check enhancement: assign nodes through stored list of nodes


        #########################################
        ####### set SINGLE parameters of an asset
        # let's go: we are using the approach of accessing assets directly in the portfolio
        # means also, we cannot alter std assets directly

        # our example is the battery
        # let us get the battery details first
        r = client.put('http://127.0.0.1:5000/get_asset_details', json='battery')
        assert r.status_code == 200
        details = json.loads(r.text)
        # details['arguments'] shows us that there is a parameter
        # cap_in_, which is of type float
        # parameters shows it has the value 1
        print(details['parameters']['cap_in'])
        # details['doc'] tells us the meaning

        # let us set it to 2 - 
        # [asset name, parameter address, value
        arg = ['battery', 'cap_in', 2]
        r = client.put('http://127.0.0.1:5000/set_asset_parameter', json=arg)
        assert r.status_code == 200

        ## check
        r = client.put('http://127.0.0.1:5000/get_asset_details', json='battery')
        assert r.status_code == 200
        details = json.loads(r.text)
        print(details['parameters']['cap_in'])

        r = client.put('http://127.0.0.1:5000/get_data', json = 'std_nodes')
        assert r.status_code == 200
        obj_std_nodes = eao.serialization.load_from_json(json.loads(r.text))
        print('****nodes now:')
        for n in obj_std_nodes: print(n.name)

        #### simplify node management --- 
        # (1) Nodes normally of type Node
        type(a1.nodes[0])
        print('old node: '+a1.nodes[0].name)
        # (2) replace as example, manage nodes by names
        a1.nodes[0] = 'node_power_2'
        js = eao.serialization.to_json(a1)
        r = client.put('http://127.0.0.1:5000/set_nodes_from_list', json = js)
        assert r.status_code == 200
        a1b = eao.serialization.load_from_json(r.text)
        print('old node: '+a1b.nodes[0].name)
    

###########################################################################################################
###########################################################################################################
###########################################################################################################

# if __name__ == '__main__':
#     flask_unittest.main()

from flask import Flask, request
import json
import eaopack as eao
import logging
import numpy as np
import typing
import copy

## standard info
file_nodes  = 'std_nodes.json'
file_assets = 'std_assets.json'
max_optim_steps = 96*5 # 5 days 15min

logging.basicConfig(filename='eao.log', encoding='utf-8', level=logging.DEBUG)
logging.info('**** Hi! New eao ession')

################################################################
### data recorder
# using global variables for data (until database is in place)
data = dict()
def recorder(key=None, in_data= None, reset:bool = False):
    """ record data

    Args:
        key (str, optional): key of the data, If None: retrieve keys
        in_data (any, optional): data to be stored. If None: retrieve data

        keys
        * portf
        * portf_nodes
        * portf_assets
        * portf_asset_names
        * timegrid
        * time_series_data
        * std_nodes
        * std_assets
    """
    global data

    if reset:
        data = dict()
        return 'ok'

    if key is None:
        return list(data)
    
    if not in_data is None:  # store
        data[key] = in_data
        if key == 'portf':
            obj = eao.serialization.load_from_json(in_data)
            if not isinstance(obj, eao.portfolio.Portfolio):
                logging.error('error. no portfolio')
                raise ValueError('error. no validportfolio passed')
            data['portf_assets']      = eao.serialization.to_json(obj.assets)
            data['portf_asset_names'] = obj.asset_names
            data['portf_nodes']       = eao.serialization.to_json(obj.nodes)
        return 'ok'
    else: # get
        if key in data:
            return data[key]
        else:
            logging.info('recorder. tried to retrieve  '+key+'  not existent')
            return None
        

#  launch server ###############################################
app = Flask(__name__)

@app.route('/')
def index():
  return 'EAO online!'
  
@app.route('/docs')
def say_hello():
    # much more missing
    return 'Please refer to https://energyassetoptimization.github.io/EAO/'

@app.route('/reset')
def reset():
    """ Resetting all temporarily stored data"""
    logging.info('resetting all temp data')
    recorder(reset= True)
    #  load standard data ##########################################        
    logging.info('loading std data')
    recorder(key='std_nodes', in_data= eao.serialization.to_json(eao.serialization.load_from_json(file_name=file_nodes)))
    recorder(key='std_assets', in_data= eao.serialization.to_json(eao.serialization.load_from_json(file_name=file_assets)))
    return 'done reset', 200

@app.route('/get_data_keys', methods=['GET'])
def send_data_keys():
    """ get keys of stored data """
    return json.dumps(recorder())

@app.route('/set_portf', methods=['PUT'])
def receive_portf():
    """ setup problem (1) send portfolio to eao server """
    try:
        data = request.get_json()
        # try to translate to portfolio
        try:
            portf = eao.serialization.load_from_json(data)
            if not isinstance(portf, eao.portfolio.Portfolio): raise ValueError('no portfolio')
            recorder('portf', data)
        except:
            s = "no valid portfolio json"
            logging.error(s)
            return s, 400
        if not isinstance(portf, eao.portfolio.Portfolio):
            s = "no portfolio, but of type "+str(type(portf))
            logging.error(s)
            return s, 400        
        logging.info('received portfolio')
        return "Done", 200       
    except:
        s = 'error, could not parse data'
        logging.error(s)
        return s, 400

@app.route('/add_std_node', methods=['PUT'])
def add_std_node():
    """ add new node to std_nodes """
    try:
        data = request.get_json()
        # try to translate to portfolio
        try:
            obj = eao.serialization.load_from_json(data)
            if not isinstance(obj, eao.basic_classes.Node): raise ValueError('no valid node given')
            # get std_nodes
            nodes = recorder('std_nodes')
            nodes = eao.serialization.load_from_json(nodes)
            # go through - delete old node with same name and add
            my_name = obj.name
            new_nodes = [obj]
            for n in nodes:
                if n.name != my_name: new_nodes.append(n)
            recorder('std_nodes', eao.serialization.to_json(new_nodes))
        except:
            s = "no valid node json"
            logging.error(s)
            return s, 400
        if not isinstance(obj, eao.basic_classes.Node):
            s = "no node, but of type "+str(type(obj))
            logging.error(s)
            return s, 400        
        s = 'received node and added (or replaced) to std_nodes'
        logging.info(s)
        return s, 200       
    except:
       s = 'error, could not parse data'
       logging.error(s)
       return s, 400

@app.route('/del_std_node', methods=['PUT'])
def del_std_node():
    """ delete node from list of std_nodes and store in recorder """
    key = request.get_json()
    nodes = recorder('std_nodes')
    nodes = eao.serialization.load_from_json(nodes)
    deleted = False
    new_nodes = []
    for a in nodes:
        logging.info(a.name)
        if a.name == key: 
            deleted = True
        else:
            new_nodes.append(a)
    if deleted:
        logging.info('deleted node '+key)
        recorder(key = 'std_nodes', in_data = eao.serialization.to_json(new_nodes))
        return 'done', 200
    else:
        s = 'node not found for deletion: '+key
        logging.info(s)
        return s, 200

@app.route('/set_timegrid', methods=['PUT'])
def receive_timegrid():
    """ setup problem (2) send timegrid to eao server """
    try:
        data = request.get_json()
        # try to translate to portfolio
        try:
            obj = eao.serialization.load_from_json(data)
            if not isinstance(obj, eao.basic_classes.Timegrid): raise ValueError('no valid timegrid')
            recorder('timegrid', data)
        except:
            s = "no valid timegrid json"
            logging.error(s)
            return s, 400
        if not isinstance(obj, eao.basic_classes.Timegrid):
            s = "no timegrid, but of type "+str(type(obj))
            logging.error(s)
            return s, 400        
        logging.info('received timegrid')
        return "Done", 200       
    except:
       s = 'error, could not parse data'
       logging.error(s)
       return s, 400

@app.route('/set_time_series_data', methods=['PUT'])
def receive_input_ts_data():
    """ setup problem (3) send price and other data to eao server """    
    data = request.get_json()
    if isinstance(data, str):    ## if json is given should be of eao.Timeseries type
        try:
            # try to translate to time series
            try:
                obj = eao.serialization.load_from_json(data)
                recorder('time_series_data', data)
            except:
                s = "no valid time series json"
                logging.error(s)
                return s, 400
            logging.info('received time series data')
            return "Done", 200       
        except:
            s = 'error, could not parse data'
            logging.error(s)
            return s, 400
    elif isinstance(data, dict): # likely given as dict of list of values
        for k in data:
            try:
                data[k] = np.asarray(data[k])
            except:
                s = "no valid time series data (dict of lists)"
                logging.error(s)
                return s, 400
        s = eao.serialization.to_json(data)
        recorder('time_series_data', s)
        logging.info('received time series data')
        return "Done", 200       
    else:
        s = 'passed unknown type to set_time_series_data'
        logging.error(s)
        return s, 400        
    
@app.route('/get_data', methods=['PUT'])
def send_data():
    """ retrieve specified data from server to client """
    try:
        s = json.dumps(recorder(request.get_json()))
    except:
        try: 
            k = request.get_json()
        except: 
            k = 'error'
        s = 'error. requested data'+ k + ' could not be retrieved'
        return s, 400
    return s, 200
    
@app.route('/optimize', methods=['GET'])
def optimize():
    """ (3) GO! """
    try:
        tg      = eao.serialization.load_from_json(recorder('timegrid'))
        portf   = eao.serialization.load_from_json(recorder('portf'))
        ts_data = eao.serialization.load_from_json(recorder('time_series_data'))
    except:
        s = 'could not load data for optimization'
        logging.error(s)
        return s, 400
    # check max time
    if tg.T > max_optim_steps:
        s = 'max number of time steps for optimization exceeded (computation time limit)'
        logging.error(s)
        return s,400
    try:
        op = portf.setup_optim_problem(prices = ts_data, timegrid = tg)
    except:
        s = 'error - could not set up problem'
        logging.error(s)
        return s, 400
    try:
        res = op.optimize()
    except:
        s = 'error - could not set up problem'
        logging.error(s)
        return s, 400
    try:
        if isinstance(res, str):
            logging.error(s)
            return res, 400
        else:
            out = eao.io.extract_output(portf, op, res)
            ### collect results neatly for easy json
            send = {}
            send['total value'] = res.value
            send['time_index']  = list(out['dispatch'].index.strftime('%Y-%m-%d %H:%M:%S'))
            for col in out['dispatch'].columns:
                send[col] = list(out['dispatch'][col])
            return send
    except:
        s = 'error - could not extract data'
        logging.error(s)
        return s, 400

def get_obj(key = 'portf'):
    """ retrieve stored data object by data key """    
    obj = recorder(key = key)
    if obj is None: 
        s = key+' not stored'
        logging.error(s)
        return s
    try:
        obj = eao.serialization.load_from_json(obj)
    except:
        s = 'invalid json'
        logging.error(s)
        return s
    return obj

@app.route('/get_asset_details', methods=['PUT'])
def get_asset_details():
    """ get details for a specific asset that is part of the portfolio (arg: asset name)"""
    key = request.get_json()
    if not isinstance(key, str):
        s = 'get asset details - requires asset name'
        logging.error(s)
        return s, 400
    portf = get_obj('portf')
    if not isinstance(portf, eao.portfolio.Portfolio):
        logging.error('no valid porftolio in recorder')
        return portf, 400
    if not key in portf.asset_names:
        s = 'get asset details -  asset name not in portfolio'
        logging.error(s)
        return s, 400
    a = portf.get_asset(key)
    params, param_dict  = eao.io.get_params_tree(a)
    out = {'parameters': param_dict, 'parameter_tree':params}
    out['doc'] = a.__init__.__doc__
    args  = typing.get_type_hints(a.__init__)
    for k in args:
        args[k] = str(args[k])
    out['arguments'] = args

    return out, 200

@app.route('/set_asset_parameter', methods=['PUT'])
def set_asset_details():
    """ edit parameter of specific asset
        arg
        [
        asset_name in portfolio (str)
         parameter tree address (list)
         value  
         ]
    """
    arg = request.get_json()
    if not isinstance(arg, list):
        s = 'parameter for setting parameters must be list of asset_name, parameter address and value'
        logging.error(s)
        return s,400
    if not isinstance(arg[0], str):
        s = 'get asset details - requires asset name'
        logging.error(s)
        return s, 400
    portf = get_obj('portf')
    if not isinstance(portf, eao.portfolio.Portfolio):
        logging.error('no valid porftolio in recorder')
        return portf, 400
    if not arg[0] in portf.asset_names:
        s = 'get asset details -  asset name not in portfolio'
        logging.error(s)
        return s, 400
    # get assets and change right asset
    assets = portf.assets
    idx = portf.asset_names.index(arg[0])
    assets[idx] = eao.io.set_param(assets[idx],arg[1], arg[2])
    portf = eao.portfolio.Portfolio(assets)
    try:
        recorder(key = 'portf', in_data=eao.serialization.to_json(portf))
    except:
        s = 'could not set parameter'
        logging.info(s)
        return s, 400

    s = 'successfully set parameter and stored in portfolio'
    logging.info(s)
    return s, 200

@app.route('/get_portf_details', methods=['GET'])
def get_portf_details():
    """ get details for the portfolio"""
    portf = get_obj('portf')
    if not isinstance(portf, eao.portfolio.Portfolio):
        s = 'no valid portfolio stored'
        logging.error(s)
        return s, 400
    params, param_dict  = eao.io.get_params_tree(portf)
    out = {'parameters': param_dict, 'parameter_tree':params}
    out['doc'] = portf.__init__.__doc__
    args  = typing.get_type_hints(portf.__init__)
    for k in args:
        args[k] = str(args[k])
    out['arguments'] = args

    return out, 200

@app.route('/get_object_details', methods=['PUT'])
def get_object_details():
    key = request.get_json()
    # So the idea of getting to understand eao logic in a gui, for example
    # would be to 
    # (1) check   typing.get_type_hints(eao.assets.Contract.__init__)
    #     to get the input variables
    # (2) check the details of specific classes such as node, unit, ...
    #     typing.get_type_hints(eao.basic_classes.StartEndValueDict)
    #     typing.get_type_hints(eao.basic_classes.Unit.__init__)
    #     typing.get_type_hints(eao.basic_classes.Node.__init__)
    if key is None:
        # info
        return " Covering the following classes. Give key: ['Node', 'Unit', 'Timegrid', 'StartEndValue'] --  __class__ / asset_type name (see JSONs)"
    try:
        if   key.lower() == 'node':          s = typing.get_type_hints(eao.basic_classes.Node.__init__)
        elif key.lower() == 'unit':          s = typing.get_type_hints(eao.basic_classes.Unit.__init__)
        elif key.lower() == 'timegrid':      s = typing.get_type_hints(eao.basic_classes.Timegrid.__init__)    
        elif key.lower() == 'startendvaluedict': s =  typing.get_type_hints(eao.basic_classes.StartEndValueDict)
        else: # __class__ name or asset_type
            try:
                if   key in vars(eao.assets):        obj = vars(eao.assets)[key]
                elif key in vars(eao.basic_classes): obj = vars(eao.basic_classes)[key]
                elif key in vars(eao.portfolio):     obj = vars(eao.portfolio)[key]
                elif key in vars(eao.serialization): obj = vars(eao.serialization)[key]
                elif key in vars(eao.optimization):  obj = vars(eao.optimization)[key]
                else: 
                    s = key + ' not found in objects'
                    logging.error(s)
                    return s, 400
                s = typing.get_type_hints(obj.__init__)
            except:
                s = 'unable to get_object_details for '+str(key)
                logging.error(s)
                return s, 400
        if isinstance(s, dict):
            for k in s:
                s[k] = str(s[k])
            s = json.dumps(s)
    except:
        s = 'error. could not retrieve object details '
        logging.error(s)
        return s, 400
    return s, 200

@app.route('/portf_delete_asset', methods=['PUT'])
def portf_del_asset():
    """ delete asset from portfolio and store in recorder """
    key = request.get_json()
    portf = get_obj('portf')
    if not isinstance(portf, eao.portfolio.Portfolio):
        logging.error('no valid porftolio in recorder')
        return portf, 400
    assets = []
    deleted = False
    for a  in portf.assets:
        if a.name == key: 
            deleted = True
        else:
            assets.append(a)
    portf = eao.portfolio.Portfolio(assets)
    if deleted:
        logging.info('deleted asset '+key)
        recorder(key = 'portf', in_data = eao.serialization.to_json(portf))
        return 'done', 200
    else:
        logging.info('asset not found for deletion: '+key)
        return 'asset not found, ignored', 200

@app.route('/portf_add_asset', methods=['PUT'])
def portf_add_asset():
    """ add asset to portfolio and store in recorder """
    key = request.get_json()
    portf = get_obj('portf')
    if not isinstance(portf, eao.portfolio.Portfolio):
        s = 'no valid porftolio in recorder'
        logging.error(s)
        return s, 400
    assets = portf.assets
    a = eao.serialization.load_from_json(key)
    if not isinstance(a, eao.assets.Asset):
        s = 'no valid asset passed'
        logging.error(s)    
        return s, 400
    assets.append(a)
    portf = eao.portfolio.Portfolio(assets)
    logging.info('added asset '+a.name)
    recorder(key = 'portf', in_data = eao.serialization.to_json(portf))
    return 'done', 200

@app.route('/set_all_asset_parameters', methods=['PUT'])
def set_all_asset_params():
    """ set all parameters of an asset (directly in the portfolio)
        this should be the most direct way to manage assets 
        arg  [asset name, parameter dict] """
    arg = request.get_json()
    if not isinstance(arg, list):
        s = 'parameter for setting parameters must be list of asset_name, parameter address and value'
        logging.error(s)
        return s,400
    if not isinstance(arg[0], str):
        s = 'get asset details - requires asset name'
        logging.error(s)
        return s, 400
    portf = get_obj('portf')
    if not isinstance(portf, eao.portfolio.Portfolio):
        logging.error('no valid porftolio in recorder')
        return portf, 400
    if not arg[0] in portf.asset_names:
        s = 'get asset details -  asset name not in portfolio'
        logging.error(s)
        return s, 400
    # get assets and change right asset
    assets = portf.assets
    idx = portf.asset_names.index(arg[0])
    # simple task, since we can pass on all parameters, creating the asset from scratch
    try:
        assets[idx] = eao.serialization.load_from_json(json.dumps(arg[1]))
    except:
        s = 'could not deserialize asset '+arg[0]
        logging.info(s)
        return s, 400
        
    # save back in portfolio and store
    portf = eao.portfolio.Portfolio(assets)
    try:
        recorder(key = 'portf', in_data=eao.serialization.to_json(portf))
    except:
        s = 'could not set parameter'
        logging.info(s)
        return s, 400


    s = 'done setting all parameters in asset '+arg[0]
    logging.info(s)
    return s, 200

reset() ### delete global vars

############## specific: manage nodes
# provide the functionality to refer to nodes by their names
# normally
# asset.nodes  is list of Nodes
#
# allow user to provice
# asset.nodes = [node_name1, node_name2]
#
# here we replace the node_names from nodes from a given node list

def fill_node_from_name(asset:eao.assets.Asset, nodes:list[eao.basic_classes.Node]):
    """ set nodes in asset by node names"""
    # get available node names
    asset = copy.deepcopy(asset)
    n_names = []
    for n in nodes:
        n_names.append(n.name)
    for i,n in enumerate(asset.nodes):
        if isinstance(n, str):
            try:
                idx = n_names.index(n)
            except:
                s = 'name of node not found'
                raise ValueError(s)
            asset.nodes[i] = nodes[idx]
        elif isinstance(n, eao.basic_classes.Node): pass
        else: raise ValueError('not a valid node')
    return asset

@app.route('/set_nodes_from_list', methods=['PUT'])
def set_nodes_from_list():
    """ set all parameters of an asset (directly in the portfolio)
        this should be the most direct way to manage assets 
        arg  [asset name, parameter dict] 
        args:
           asset as input
        returns 
           asset with replaced nodes taken from protf nodes and std nodes """
    arg = request.get_json()  # no
    a = eao.serialization.load_from_json(arg)
    if not isinstance(a, eao.assets.Asset):
        s = 'no valid asset passed'
        logging.error(s)    
        return s, 400
    # get all available nodes
    std_nodes = eao.serialization.load_from_json(recorder(key = 'std_nodes'))    
    if not isinstance(std_nodes, list): 
        std_nodes = []
    portf_nodes = eao.serialization.load_from_json(recorder(key = 'portf_nodes'))    
    if not isinstance(portf_nodes, list): 
        portf_nodes = []
    nodes = std_nodes+portf_nodes

    # replace names with nodes
    a = fill_node_from_name(a, nodes)
    return eao.serialization.to_json(a), 200

############## get network for portfolio

### get encoded info
@app.route('/get_network', methods=['GET'])
def get_network():
    """ get network info for portfolio
        returns 
           encoded networkx output for portfolio: nodes, edges, labels, ... """
    try:
        portf   = eao.serialization.load_from_json(recorder('portf'))
        res = eao.network_graphs.create_graph(portf=portf, no_image_output=True)
        # positions or other elements may be given as arrays - make lists to make them serializable
        for k in res:
            if isinstance(res[k], dict):
                for kk in res[k]:
                    if isinstance(res[k][kk], np.ndarray): res[k][kk] = list(res[k][kk])
            if isinstance(res[k], list):
                for ii, kk in enumerate(res[k]):
                    if isinstance(kk, np.ndarray): res[k][ii] = list(kk)
                
    except:
        s = "could not create portfolio's network chart"
        logging.error(s)
        return s, 400
    return res, 200


def create_app():
    return app

#######################################################
if __name__ == "__main__":
    app.run(debug=True)


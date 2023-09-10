###### define standard and predefined objects of EAO server
import eaopack as eao

file_nodes  = 'std_nodes.json'
file_assets = 'std_assets.json'


### nodes for standard commodities and units
nodes = []
MW_MWh = eao.basic_classes.Unit(volume='MWh',
                                flow='MW',
                                factor=1)

nodes.append( eao.basic_classes.Node(name = 'node_power',
                                     commodity= 'power',
                                     unit = MW_MWh) )

nodes.append( eao.basic_classes.Node(name = 'node_heat',
                                     commodity= 'heat',
                                     unit = MW_MWh))

nodes.append( eao.basic_classes.Node(name = 'gas',
                                     commodity= 'gas',
                                     unit = MW_MWh))

nodes.append( eao.basic_classes.Node(name = 'node_power_2',
                                     commodity= 'power',
                                     unit = MW_MWh) )

eao.serialization.to_json(file_name=file_nodes, obj=nodes)

### std assets
assets = []
assets.append( eao.assets.SimpleContract(name = 'std_contract',
                                         nodes= nodes[0],
                                         price = 'price_tag',
                                         max_cap = 10,
                                         min_cap = -10 ))

assets.append( eao.assets.Storage(       name = 'battery',
                                         nodes= nodes[0],
                                         cap_in  = 1,
                                         cap_out = 1,
                                         eff_in = 0.9,
                                         start_level = 0,
                                         end_level = 0,
                                         block_size = 'd',
                                         size = 4))

assets.append( eao.assets.MultiCommodityContract(name = 'power_to_heat',
                                         nodes= [nodes[0], nodes[1]],
                                         extra_costs = 0,
                                         max_cap = 10,
                                         min_cap = 0,
                                         factors_commodities= [-1,4]))

assets.append( eao.assets.Transport(name = 'transport', 
                                    efficiency = 0.95, 
                                    nodes = [nodes[0], nodes[3]]))

assets.append(eao.assets.MultiCommodityContract(name = 'simple CHP', 
                                                extra_costs = 'CHP_costs_tag', 
                                                min_cap= 0, 
                                                max_cap=1, 
                                                nodes = [nodes[0], nodes[1]], 
                                                factors_commodities=[0.8, 2.2]))

assets.append( eao.assets.CHPAsset(name='CHP with gas',
                                nodes=(nodes[0], nodes[1], nodes[2]),
                                min_cap=1.,
                                max_cap=10.,
                                start_costs=1.,
                                running_costs=5.,
                                conversion_factor_power_heat= 0.2,
                                max_share_heat= 1,
                                start_fuel = 10,
                                fuel_efficiency= .5,
                                consumption_if_on= .1) )

eao.serialization.to_json(file_name=file_assets, obj=assets)
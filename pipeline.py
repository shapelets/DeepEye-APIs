from .deepeye_pack import deepeye
from shapelets.data import sandbox, ReadCSVOptions
from shapelets.apps import DataApp
from shapelets.native import DataType


types_mapping = {'Date':'date',
                 'String[*]':'varchar',
                 'Float64':'float',
                 'Int64':'int'}

dp = deepeye('test') # the name here doesn't actually matter


file = './datasets/FlightDelayStatistics2015.csv'
#file = './datasets/SummerOlympic_1896_2008.csv'
#file = './datasets/electricityConsumptionOfEasternChina.csv'
#file = './datasets/happinessRanking(2015-2016).csv'
#file = './datasets/Foreign Visitor Arrivals By Purpose(Jan-Dec 2015).csv'
#file = './datasets/HollywoodsMostProfitableStories.csv'
#file = './datasets/MostPopularBaby_Names(NewYork).csv'
#file = './datasets/titanicPassenger.csv'

sb = sandbox()
relation_name = "my_relation"
my_relation = sb.from_csv(relation_name,[file])

dp.csv_dataframe = my_relation.execute().to_pandas().dropna(axis=0, how='any')
dp.table_info("", my_relation.schema.names, [types_mapping[str(item)] for item in my_relation.schema.types])
dp.import_method = 'csv'

# choose one ranking function
#dp.partial_order()
#dp.learning_to_rank()
dp.diversified_ranking()

app = DataApp()
for chart in dp.show_visualizations()._charts:
    app.echart(chart=chart.dump_options())









from flask import Flask,request,render_template,redirect,url_for,jsonify,Response
import reviews
import logger
import threading
from flask_cors import CORS, cross_origin
import db
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io


free_status = True

rows = {}

collection_name=None
app= Flask(__name__)


log = logger.setup_app_level_logger(file_name = 'app_debug.log')


class threadClass:

    def __init__(self, searchString):
        self.searchString = searchString
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution

    def run(self):
        free_status = False
        global collection_name
        collection_name = reviews.getReviewsToDisplay(searchString=self.searchString, username='mongotest',password='mongo123')
        log.info("Thread run completed")
        free_status = True



@app.route('/',methods=['POST','GET'])
@cross_origin()
def home():
    if request.method == 'POST':
        searchstring = request.form['content'].replace(" ","-")
        log.info('the search string value is '+searchstring)
        searchresult = reviews.navigatetoapp(searchstring)
        if(searchresult == "Unable to find details for searched product"):
            return render_template('tryagain.html')
        else:
            mongoClient = db.MongoDBManagement(username='mongotest', password='mongo123')
            if mongoClient.isCollectionPresent(collection_name=searchstring, db_name="CarDekhoWebScrapping"):
                log.info('Mongo collection is present')
                response = mongoClient.findAllRecords(db_name="CarDekhoWebScrapping", collection_name=searchstring)
                review= [i for i in response]
                log.info('the review data is '+str(review))
                result = [review[i] for i in range(0, len(review))]
                reviews.saveDataFrameDatatoFile("static/scrapper_data.csv",pd.DataFrame(result))
                log.info("Data saved in scrapper file")
                log.info("the review result is "+str(result))
                return render_template('reviews.html',rows=review)
                # else:
                #     review_count = len(reviews)
                #     threadClass(expected_review=expected_review, searchString=searchstring,
                #                  review_count=review_count)
                #     logger.info("data saved in scrapper file")
                #     return redirect(url_for('feedback'))
            else:
                log.info('collection not found so getting details')
                global collection_name
                collection_name = reviews.getReviewsToDisplay(searchstring,'mongotest','mongo123')
                log.info('the collection name is '+str(collection_name))
                return redirect(url_for('feedback'))
    else:
        return render_template('index.html')

@app.route('/feedback', methods=['GET'])
@cross_origin()
def feedback():
    try:
        global collection_name
        if collection_name is not None:
            log.info('in the if condition and collection name is not None')
            mongoClient = db.MongoDBManagement(username='mongotest', password='mongo123')
            rows = mongoClient.findAllRecords(db_name="CarDekhoWebScrapping", collection_name=collection_name)
            log.info('the rows are '+str(rows))
            review = [i for i in rows]
            log.info('the review values are '+str(review))
            dataframe = pd.DataFrame(review)
            reviews.saveDataFrameDatatoFile(file_name="static/scrapper_data.csv", dataframe=pd.DataFrame(dataframe))
            collection_name = None
            return render_template('reviews.html', rows=review)
        else:
            log.info('in the else loop and collection name is None')
            return render_template('tryagain.html')
    except Exception as e:
        raise Exception("(feedback) - Something went wrong on retrieving feedback.\n" + str(e))
           

@app.route("/graph", methods=['GET'])
@cross_origin()
def graph():
    return redirect(url_for('plot_png'))


@app.route('/a', methods=['GET'])
def plot_png():
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')


def create_figure():
    data = pd.read_csv("static/scrapper_data.csv")
    dataframe = pd.DataFrame(data=data)
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    xs = dataframe['Car_Name']
    ys = dataframe['Rating_Title']
    axis.scatter(xs, ys)
    return fig


if(__name__=='__main__'):
    app.run(debug=True) 
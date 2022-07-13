from flask import Flask,Request
from urllib.request import Request, urlopen
import requests
from bs4 import BeautifulSoup as bs
import logger
import numpy as np
import pandas as pd
import db


log = logger.get_logger("reviews.py")
  
def navigatetoapp(searchstring):
        app_url = "https://www.cardekho.com/user-reviews/"+searchstring #maruti-vitara-brezza
        log.info('the url to navigate is '+app_url)
        req = Request(app_url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urlopen(req)
        global reviewpage 
        reviewpage= resp.read()
        if "ratingvalue" in str(reviewpage):
                global productname
                productname = searchstring.replace("-"," ")
                log.info('satisfied the if condition and able to find product')
                return "Able to find the product"
        else:
                log.info('in the else condition and cannot find product')
                return "Unable to find details for searched product"

def get_reviews_from_ui():
        print(reviewpage)
        log.info('the review page details are '+str(reviewpage))
        reviewpage_html =bs(reviewpage)
        log.info(str(reviewpage_html))
        product_name = (reviewpage_html.text).split("Reviews -")[0]
        log.info('the product name is '+str(product_name))
        review_value = reviewpage_html.find('span',{'class':'ratingvalue'}).text
        log.info('the review value is '+str(review_value))
        reviews_title =reviewpage_html.findAll('div',{'class':'contentspace'})
        log.info('the review title is '+str(reviews_title))
        titles,review_desc,review_authorname,reviewer_name,user_rating,review_date,review_datelist=([] for i in range(7))
        for i in range(0,len(reviews_title)):
                titles.append(str(reviews_title[i].h3.a.text))
                log.info('the titles are '+str(titles))
        review_content =  reviewpage_html.findAll('p',{'class':'contentheight'})
        log.info('the review content are '+str(review_content))
        for i in range(0,len(review_content)):
                review_desc.append(str(review_content[i].span.text))
                log.info('the review desc are '+str(review_desc))
        review_author =  reviewpage_html.findAll('div',{'class':'authorSummary'})
        log.info('the review author  are '+str(review_author))
        for i in range(0,len(review_author)):
                review_authorname.append(review_author[i].findAll('div',{'class':'name'}))
                log.info('the review author names are '+str(review_authorname))
        review_name=[]
        review_name=[ele for ele in review_authorname if ele != []]
        log.info('the review names are '+str(review_name))
        for i in range(0,len(review_name)):
                reviewer_name.append((review_name[i][0].text).split('By ')[1])
                log.info('the review names are '+str(reviewer_name))
        car_price =  str(reviewpage_html.findAll('div',{'class':'price'})[0].span.text).replace('*Get On Road Price','')
        log.info('the car price is '+str(car_price))
        title = str(reviewpage_html.findAll('div',{'class':'title'})[0].a.text)
        log.info('the title is '+str(title))
        user_all_ratings = reviewpage_html.findAll('div',{'class':'starRating'})
        log.info('the user all rating is '+str(user_all_ratings))
        for  i in range(0,len(user_all_ratings)):
                user_rating.append(len(user_all_ratings[i].findAll('span',{'class':'icon-star-full-fill'}))+int(len(user_all_ratings[i].findAll('span',{'class':'icon-star-half-empty'})))/2)
        log.info('the user rating is '+str(user_rating))
        resp_list=[]
        for i in range(0,len(review_author)):
                resp_list.append(review_author[i].findAll('div',{'class':'date'}))
        log.info('the user date list is '+str(resp_list))
        review_datelist=[ele for ele in resp_list if ele != []]
        for i in range(0,len(review_datelist)):
                temp = str(review_datelist[i][0].text).replace("On: ","").split(" ")
                review_date.append(temp[0]+' '+ temp[1]+' '+ temp[2])
                log.info('the review date is '+str(review_date))
        log.info('the length of arrays are '+str(len(titles))+' '+str(len(review_desc))+' '+str(len(reviewer_name))+' '+str(len(user_rating))+' '+str(len(review_date)))
        rating_dict = dict(Car_Name= np.array(product_name,dtype=object), OverAll_Rating= np.array(review_value,dtype=object), Price= np.array(car_price,dtype=object), Rating_Title=np.array(titles,dtype=object),
                             Reviews_Description=np.array(review_desc,dtype=object), Review_Author= np.array(reviewer_name,dtype=object), User_Rating= np.array(user_rating,dtype=object), Review_Date= np.array(review_date,dtype=object) )
        log.info('the rating dictionary is '+str(rating_dict))
        df = pd.DataFrame.from_dict(rating_dict)   
        log.info('the data frame data is '+str(df)) 
        return df


def saveDataFrameDatatoFile(file_name,dataframe):
        try:
                dataframe.to_csv(file_name)
        except Exception as e:
                raise Exception(f"(saveDataframetofile)  - Unable to save data to the file.\n" + str(e))


def getReviewsToDisplay(  searchstring, username, password):
        try:
                mongoClient = db.MongoDBManagement(username, password)
                db_search = mongoClient.findfirstRecord(db_name = "CarDekhoWebScrapping",collection_name=productname,
                                                                query="{'product_name': productname}")
                print(db_search)
                log.info('the db_search value is '+str(db_search))
                if db_search is not None:
                        print("Yes Present "+str(len(db_search)))
                        log.info("Yes Present "+str(len(db_search)))
                else:
                        log.info("Not Present ")
                        dataframe = get_reviews_from_ui()
                        result = saveDataFrameDatatoFile("static/scrapper_data.csv",dataframe)
                        mongoClient.insertRecordFromCSVFile(db_name="CarDekhoWebScrapping",
                                                             collection_name=searchstring,
                                                             csv_file="static/scrapper_data.csv",header=list(dataframe.columns))
                return searchstring
        except Exception as e:
            raise Exception(f"(getReviewsToDisplay) - Something went wrong on yielding data.\n" + str(e))







        

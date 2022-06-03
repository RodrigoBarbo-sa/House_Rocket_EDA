# -*- coding: utf-8 -*-
"""
Created on Mon Apr  4 16:15:01 2022

@author: brodr
"""

import geopandas
import streamlit as st
import pandas    as pd
import numpy     as np
import folium
#import matplotlib.pyplot as plt

#from datetime import datetime, time

from streamlit_folium import folium_static
from folium.plugins   import MarkerCluster

import plotly.express as px 


# ------------------------------------------
# settings
# ------------------------------------------
st.set_page_config( layout='wide' )


# ------------------------------------------
# Helper Functions
# ------------------------------------------
@st.cache( allow_output_mutation=True )
def get_data( path ):
    df = pd.read_csv( path )
    df = df[df['bedrooms']!=0]
    df = df[df['bathrooms']!=0]
    df = df[df['bedrooms'] != 33]
    df['date'] = pd.to_datetime(df['date'])

    return df


@st.cache( allow_output_mutation=True )
def get_geofile( url ):
    geofile = geopandas.read_file( url )

    return geofile

def data_overview( til ):
    f_attributes = st.sidebar.multiselect( 'Enter columns', df.columns ) 
    f_zipcode = st.sidebar.multiselect( 'Enter zipcode', df['zipcode'].unique() )

    st.title( 'Visão geral dos dados' )

    if ( f_zipcode != [] ) & ( f_attributes != [] ):
        til = df.loc[df['zipcode'].isin( f_zipcode ), f_attributes]

    elif ( f_zipcode != [] ) & ( f_attributes == [] ):
        til = df.loc[df['zipcode'].isin( f_zipcode ), :]

    elif ( f_zipcode == [] ) & ( f_attributes != [] ):
        til = df.loc[:, f_attributes]

    else:
        til = df.copy()

    st.write( til.head(20) )
    
    return None
    

def what_view(df):
    
    c1, c2 = st.columns((1, 1) )  
    wtf_view =  df[['price','waterfront']].groupby('waterfront').mean().reset_index()
    fig = px.bar(wtf_view, x="waterfront", y="price")
    c1.header('G1 - Preço Médio segundo critério de vista para a água')
    c1.write(fig)
    
    yr_built_p =  df[['price','yr_built']].groupby('yr_built').mean().reset_index()
    fig = px.line(yr_built_p, x = 'yr_built', y = 'price')
    c2.header('G2 - Preço Médio por ano de construção do imóvel ')
    c2.write(fig)
    
    return None

def sazonalidade(df):
    

    df['sell_year'] = df['date'].dt.year
    
    df['sell_month'] = df['date'].dt.month
    
    
    
    df['sell_year_month'] = df['date'].dt.to_period('M')
    
    sell_year_month_p =  df[['price','sell_year_month']].groupby('sell_year_month').mean().reset_index()
    sell_year_month_p = sell_year_month_p.sort_values(by=['sell_year_month'], ascending=True)
    sell_year_month_p['sell_year_month'] = sell_year_month_p['sell_year_month'].astype('str')
    #fig = plt.figure(figsize=(10, 5))
    c1, c2 = st.columns((1, 1) )
    fig = px.line(sell_year_month_p, x = 'sell_year_month', y = 'price')
    c1.header('G3 - Preço Médio por mês de venda ')
    c1.write(fig)
    
    df['seasons'] = df['sell_month'].apply(lambda x: 'summer' if x in [6,7,8]
                                             else 'fall' if x in [9,10,11] 
                                             else 'winter' if x in [ 12, 1,2] 
                                             else 'spring')
    seasonality_price =  df[['price','seasons']].groupby('seasons').mean().reset_index()
    fig = px.bar(seasonality_price, x="price", y="seasons", color="seasons", text_auto=True)
    c2.header('G4 - Preço Médio por estação de venda ')
    c2.write(fig)

def grade_price(df):
    
    c1, c2 = st.columns((1, 1) )
    condition_price =  df[['price','grade']].groupby('grade').median().reset_index()
    fig = px.line(condition_price, x = 'grade', y = 'price')
    c1.header('G5 - Preço Médio por nota do imóvel ')
    c1.write(fig)
    
    df['renovated'] = df['yr_renovated'].apply(lambda x: 0 if x == 0
                                         else 1)
    renovated_p = df[['price','renovated']].groupby('renovated').mean().reset_index()
    comparison = renovated_p.price / renovated_p.price[0]
    renovated_p['comparison'] = comparison
    fig = px.bar(renovated_p, x="renovated", y="price", color = 'comparison',  text_auto=True)
    c2.header('G6 - Preço Médio com e sem reforma ')
    c2.write(fig)
    
    return None
    
def price_map (df,geofile):
    st.title( 'Region Overview' )

    c1, c2 = st.columns( ( 1, 1 ) )
    c1.header( 'G7 - Portfolio Density' )

    df1 = df.sample( 10 )

    # Base Map - Folium 
    density_map = folium.Map( location=[df['lat'].mean(), df['long'].mean() ],
                              default_zoom_start=15 ) 

    marker_cluster = MarkerCluster().add_to( density_map )
    for name, row in df1.iterrows():
        folium.Marker( [row['lat'], row['long'] ], 
            popup='Sold R${0} on: {1}. Features: {2} sqft, {3} bedrooms, {4} bathrooms, year built: {5}'.format( row['price'], 
                           row['date'], 
                           row['sqft_living'],
                           row['bedrooms'],
                           row['bathrooms'],
                           row['yr_built'] ) ).add_to( marker_cluster )


    with c1:
        folium_static( density_map )


    # Region Price Map
    c2.header( 'G8 - Price Density' )

    df2 = df[['price', 'zipcode']].groupby( 'zipcode' ).mean().reset_index()
    df2.columns = ['ZIP', 'PRICE']

    geofile = geofile[geofile['ZIP'].isin( df2['ZIP'].tolist() )]

    region_price_map = folium.Map( location=[df['lat'].mean(), 
                                   df['long'].mean() ],
                                   default_zoom_start=15 ) 


    region_price_map.choropleth( data = df2,
                                 geo_data = geofile,
                                 columns=['ZIP', 'PRICE'],
                                 key_on='feature.properties.ZIP',
                                 fill_color='YlOrRd',
                                 fill_opacity = 0.7,
                                 line_opacity = 0.2,
                                 legend_name='AVG PRICE' )

    with c2:
        folium_static( region_price_map )

   
def price_area(df):
    
    fig = px.scatter(df , x = 'sqft_living', y = 'price', width = (1280))

    st.header('G9 - Preço médio por área do imóvel')
    st.write(fig)
    

    return None

def recomendations (df):
    
    grouped_selection = df[['price', 'zipcode','renovated','waterfront', 'grade']].groupby(['zipcode','renovated','waterfront', 'grade']).count().reset_index()
    
    grouped_selection = grouped_selection.rename(columns={'price': 'House_count'})
    
    grouped_selection1 = df[['price', 'zipcode','renovated','waterfront', 'grade']].groupby(['zipcode','renovated','waterfront', 'grade']).median().reset_index()
    
    grouped_selection2 = pd.merge(grouped_selection, grouped_selection1, on =['zipcode','renovated','waterfront', 'grade'], how ='inner')
    
    grouped_selection2 = grouped_selection2.rename(columns={'price': 'price_median'})
        
    df1= pd.merge(df, grouped_selection2, on =['zipcode','renovated','waterfront', 'grade'], how ='inner')
    
    df1 = df1[df1['House_count'] >= 100]
    price_diference = df1.price - df1.price_median
    df1['price_diference'] = price_diference
    
    # Ranqueando os imóveis que possuem a maior diferença de preço para a mediana de seu grupo,
    # assim saberemos quais as melhores oporunidades de compra
    df2 = df1[['zipcode','renovated','waterfront', 'grade', 'id','price', 'price_median', 'price_diference']]
    df2 = df2.sort_values(by = 'price_diference', ascending= True)
    #pd.set_option('display.max_rows', None)
    

    
    target_price = df2.price * 1.43

    df2['target_price'] = target_price
    df2['status'] = np.where(df2['target_price'] < df2['price_median'],'compra' , 'não compra')
    
    # Reordenando as colunas da tabela para uma melhor visualização 
    df2 = df2[['zipcode', 'renovated', 'waterfront', 'grade', 'id', 'price',
           'price_median', 'price_diference','target_price', 'status']]
    
    ## Vamos filtrar somente os imóveis que nosso indicador apontou para compra
    
    df3 = df2[df2['status'] == 'compra']
    st.header('Imóveis recomendados para compra')
    st.write(df3)
    
    return None
    

    
 
    

if __name__ == "__main__":
    # ETL
    path = 'kc_house_data.csv'
    url='https://opendata.arcgis.com/datasets/83fc2e72903343aabff6de8cb445b81c_2.geojson'

    # load data
    df = get_data( path )
    geofile = get_geofile( url )
    til = df
    
   
    # transform data
    
    data_overview(til)
    what_view(df)
    sazonalidade(df)
    grade_price(df)
    price_map(df,geofile)
    price_area(df)
    recomendations(df)
   
# # Import python packages
# import streamlit as st
# from snowflake.snowpark.functions import col
# import requests

# API_KEY = "KNL2dMUR1G1rFbyhMisAeSebjsZTmRFwrCNSixLD"

# # Write directly to the app
# st.title(f":cup_with_straw:  Customize Your Smoothie !:cup_with_straw:")
# st.write(
#   """Choose the Fruits you want in your custom Smoothie !"""
# )

# name_on_order = st.text_input("Name on Smoothie")
# st.write("The name on your smoothie will be: ", name_on_order)

# cnx=st.connection("snowflake")
# session = cnx.session() 
# my_dataframe=session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'))
# #st.dataframe(data=my_dataframe,use_container_width=True)

# ingredients_list=st.multiselect('Choose upto 5 Ingredient:',
#                                 my_dataframe,
#                                 max_selections=5)

# if ingredients_list:
#     ingredients_string=''
#     for fruit_chosen in ingredients_list:
#         ingredients_string+=fruit_chosen+' '
#         st.subheader(fruit_chosen+'Nutrition Information')
#         smoothiefroot_response = requests.get("https://api.nal.usda.gov/fdc/v1/foods/search?query={fruit_chosen}&api_key={API_KEY}")
#         st_df=st.dataframe(data=smoothiefroot_response.json(),use_container_width=True)


#     my_insert_stmt = """ insert into smoothies.public.orders(ingredients,name_on_order)
#                 values ('""" + ingredients_string + """','""" + name_on_order + """')"""
#     time_to_insert=st.button('Submit Order')

#     # st.write(my_insert_stmt)
#     # st.stop()
#     if time_to_insert:
#         session.sql(my_insert_stmt).collect()
#         st.success('Your Smoothie is ordered!', icon="✅")


# import streamlit as st
# from snowflake.snowpark.functions import col
# import pandas as pd
# import requests

# # USDA API Key
# API_KEY = "KNL2dMUR1G1rFbyhMisAeSebjsZTmRFwrCNSixLD"

# # Streamlit UI
# st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
# st.write("Choose the Fruits you want in your custom Smoothie!")

# # Smoothie name
# name_on_order = st.text_input("Name on Smoothie")
# st.write("The name on your smoothie will be:", name_on_order)

# # Snowflake connection
# cnx = st.connection("snowflake")
# session = cnx.session()
# my_dataframe = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"))
# fruit_list = [row["FRUIT_NAME"] for row in my_dataframe.collect()]

# # Multiselect fruits
# ingredients_list = st.multiselect(
#     "Choose up to 5 Ingredients:",
#     fruit_list,
#     max_selections=5
# )

# # Helper to fetch nutrition
# def fetch_nutrition(fruit_name):
#     url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={fruit_name}&api_key={API_KEY}"
#     response = requests.get(url)
#     if response.status_code == 200:
#         data = response.json()
#         foods = data.get("foods", [])
#         if not foods:
#             return None
#         food_nutrients = foods[0].get("foodNutrients", [])
#         if not food_nutrients:
#             return None
#         df = pd.DataFrame(food_nutrients)[["nutrientName", "value", "unitName"]]
#         df.columns = ["Nutrient", "Value", "Unit"]
#         return df
#     return None

# # Process selected fruits
# if ingredients_list:
#     ingredients_string = ""
#     for fruit in ingredients_list:
#         ingredients_string += fruit + " "
#         st.subheader(f"{fruit} Nutrition Info")
#         nutrition_df = fetch_nutrition(fruit)
#         if nutrition_df is not None:
#             st.dataframe(nutrition_df, use_container_width=True)
#         else:
#             st.warning(f"No nutrition info found for {fruit}")

#     # Submit button
#     if st.button("Submit Order"):
#         insert_stmt = f"""
#             INSERT INTO smoothies.public.orders (ingredients, name_on_order)
#             VALUES ('{ingredients_string.strip()}', '{name_on_order}')
#         """
#         session.sql(insert_stmt).collect()
#         st.success("Your Smoothie is ordered!", icon="✅")


# Import python packages
import streamlit as st
from snowflake.snowpark.functions import col
import pandas as pd
import requests

# USDA API Key
API_KEY = "KNL2dMUR1G1rFbyhMisAeSebjsZTmRFwrCNSixLD"

# Set page config
st.set_page_config(page_title="Smoothie Builder", page_icon=":cup_with_straw:", layout="centered")

# --- Title ---
st.title("🥤 Customize Your Smoothie! 🥤")
st.write("Choose the fruits you want in your custom Smoothie!")

# --- Input name ---
name_on_order = st.text_input("Name on Smoothie:")
if name_on_order:
    st.write("The name on your Smoothie will be:", name_on_order)

# --- Connect to Snowflake ---
cnx = st.connection("snowflake")
session = cnx.session()
fruit_df = session.table("smoothies.public.fruit_options").select(col("FRUIT_NAME"),col("SEARCH_ON"))
pd_df=fruit_df.to_pandas()
st.dataframe(pd_df)
st.stop()

fruit_list = [row["FRUIT_NAME"] for row in fruit_df.collect()]

# --- Select ingredients ---
ingredients = st.multiselect("Choose up to 5 ingredients:", fruit_list, max_selections=5)

# --- Nutrition + Order ---
if ingredients:
    ingredients_string = ', '.join(ingredients)

    for fruit in ingredients:
        # st.subheader(f"{fruit} Nutrition Info")
        query = fruit.lower()
        url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={query}&api_key={API_KEY}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            foods = data.get("foods", [])
            if foods and "foodNutrients" in foods[0]:
                nutrients = foods[0]["foodNutrients"]
                # df = pd.DataFrame(nutrients)[["nutrientName", "value", "unitName"]]
                # st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No nutrition info found for {fruit}")
        else:
            st.error("Failed to fetch nutrition data")

    # Submit order
    if st.button("Submit Order"):
        insert_stmt = f"""
            INSERT INTO smoothies.public.orders (ingredients, name_on_order)
            VALUES ('{ingredients_string}', '{name_on_order}')
        """
        session.sql(insert_stmt).collect()
        st.success(f"✅ Your Smoothie is ordered, {name_on_order}!")

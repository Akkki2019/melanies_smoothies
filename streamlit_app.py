# # Import python packages
# import streamlit as st
# from snowflake.snowpark.functions import col
# import requests

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
#         smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")
#         st_df=st.dataframe(data=smoothiefroot_response.json(),use_container_width=True)


#     my_insert_stmt = """ insert into smoothies.public.orders(ingredients,name_on_order)
#                 values ('""" + ingredients_string + """','""" + name_on_order + """')"""
#     time_to_insert=st.button('Submit Order')

#     # st.write(my_insert_stmt)
#     # st.stop()
#     if time_to_insert:
#         session.sql(my_insert_stmt).collect()
#         st.success('Your Smoothie is ordered!', icon="✅")



# Import python packages
import streamlit as st
import pandas as pd # Added pandas import
from snowflake.snowpark.context import get_active_session # Keep this if get_active_session is preferred for some reason, though st.connection is used below
from snowflake.snowpark.functions import col
import requests

# Wrap the main application logic in a try-except block for robust error handling
try:
    # Write directly to the app
    st.title(f":cup_with_straw: Customize Your Smoothie !:cup_with_straw:")
    st.write(
        """Choose the Fruits you want in your custom Smoothie !"""
    )

    name_on_order = st.text_input("Name on Smoothie")
    st.write("The name on your smoothie will be: ", name_on_order)

    # --- Snowflake Connection ---
    # Using st.connection as per your provided code
    cnx = st.connection("snowflake", type="sql") # Explicitly define type for clarity
    session = cnx.session()
    st.success("Successfully connected to Snowflake session!")

    # --- Function to get fruit data (with IS_AVAILABLE and SEARCH_ON) ---
    # This function is now memoized to avoid re-fetching data unnecessarily,
    # but it will re-run if its inputs change (e.g., after an update)
    @st.cache_data(ttl=600) # Cache data for 10 minutes
    def get_fruit_options_data(_session): # Pass session to the cached function
        # Fetch FRUIT_OPTIONS data including 'FRUIT_NAME', 'SEARCH_ON', and 'IS_AVAILABLE'
        return _session.table("smoothies.public.fruit_options").select(col('FRUIT_NAME'), col('SEARCH_ON'), col('IS_AVAILABLE')).to_pandas()

    # Fetch FRUIT_OPTIONS data
    pd_df = get_fruit_options_data(session) # Pass the active session
    st.success("Successfully fetched fruit options data!")

    # Filter for available fruits to display in the multiselect
    available_fruits_df = pd_df[pd_df['IS_AVAILABLE'] == True]

    # Display the full fruit options for debugging (uncommented as requested)
    st.dataframe(pd_df, use_container_width=True) 

    # Multiselect for ingredients
    # Pass the 'FRUIT_NAME' column of available fruits as a list to st.multiselect
    ingredients_list = st.multiselect(
        'Choose upto 5 Ingredient:',
        available_fruits_df['FRUIT_NAME'].tolist(), # Use tolist() to get a simple Python list of fruit names
        max_selections=5
    )

    if ingredients_list:
        ingredients_string = ''
        # List to hold fruits that need to be marked as unavailable after order
        fruits_to_mark_unavailable = [] 

        for fruit_chosen in ingredients_list:
            ingredients_string += fruit_chosen + ' '
            fruits_to_mark_unavailable.append(fruit_chosen) # Add to list for update

            # Find the corresponding SEARCH_ON value using pandas .loc
            # .iloc[0] is used because .loc can return a Series, and we just want the first (and only) value
            search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
            st.write('The search value for ', fruit_chosen, ' is ', search_on, '.')
            
            # --- API Call for Nutrition Information ---
            st.subheader(fruit_chosen + ' Nutrition Information')
            try:
                # Construct the API URL using the 'search_on' value
                # Assuming the API expects the fruit name in the URL path
                api_url = f"https://my.smoothiefroot.com/api/fruit/{search_on}" 
                smoothiefroot_response = requests.get(api_url) 
                
                # Check if the request was successful (status code 200)
                if smoothiefroot_response.status_code == 200:
                    # Try to parse as JSON
                    st_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
                else:
                    st.error(f"API request failed for {search_on} with status code: {smoothiefroot_response.status_code}")
                    st.text(f"API Response Text: {smoothiefroot_response.text}") # Display raw response text
            except requests.exceptions.RequestException as req_err:
                st.error(f"Error connecting to the API for {search_on}: {req_err}")
                st.info("Please check the API URL and your network access from Streamlit Cloud.")
            except Exception as json_err:
                st.error(f"Error parsing API response as JSON for {search_on}: {json_err}")
                st.text(f"Raw API Response Text: {smoothiefroot_response.text if 'smoothiefroot_response' in locals() else 'No response received'}")
                st.info("The API might be returning non-JSON data or an empty response.")
            # --- End API Call Section ---

        # Display the final ingredients string
        st.write("You selected: ", ingredients_string)

        # Construct the SQL insert statement for the order
        my_insert_stmt = f"""
            INSERT INTO smoothies.public.orders(ingredients, name_on_order)
            VALUES ('{ingredients_string.strip()}', '{name_on_order}')
        """
        
        # Button to submit the order
        time_to_insert = st.button('Submit Order')

        if time_to_insert:
            # Execute the order insert statement
            session.sql(my_insert_stmt).collect()
            st.success('Your Smoothie is ordered!', icon="✅")

            # --- Update IS_AVAILABLE for selected fruits ---
            if fruits_to_mark_unavailable:
                # Create a comma-separated string of fruit names for the IN clause
                fruits_str = ", ".join([f"'{f}'" for f in fruits_to_mark_unavailable])
                update_stmt = f"""
                    UPDATE smoothies.public.fruit_options
                    SET IS_AVAILABLE = FALSE
                    WHERE FRUIT_NAME IN ({fruits_str});
                """
                session.sql(update_stmt).collect()
                st.info(f"Marked {fruits_str} as unavailable.")
                
                # Clear the cache for get_fruit_options_data so it re-fetches fresh data
                get_fruit_options_data.clear()
                st.rerun() # Rerun the app to reflect the updated availability immediately

            # Display the updated orders table to confirm the write
            st.subheader("Recent Orders:")
            orders_df = session.table("smoothies.public.orders").to_pandas()
            st.dataframe(orders_df, use_container_width=True)

except Exception as e:
    st.error(f"An unexpected error occurred in your Streamlit app: {e}")
    st.error("Please ensure your Snowflake account is not locked and your Streamlit Cloud secrets are correctly configured.")
    st.info("Remember to check your 'App settings' -> 'Secrets' in Streamlit Cloud for the correct Snowflake credentials (account, user, password, role, warehouse, database, schema).")


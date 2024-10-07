import streamlit as st
import pandas as pd
import polars as pl
import base64
import os
import sys
import uuid
from datetime import datetime
from utils.data_processing import (
    get_data,
    decrypt_dataframe,
    get_unique_kommuner,
    get_unique_categories,
    filter_dataframe_by_choice,
    filter_dataframe_by_category,
    generate_organization_links,
    filter_df_by_search,
    fix_column_types_and_sort,
    format_number_european,
    round_to_million_or_billion,
    get_ai_text,
    to_excel_function,
    load_css,
    write_markdown_sidebar,
)
from utils.plots import create_pie_chart
from config import set_pandas_options, set_streamlit_options

# Apply the settings
set_pandas_options()
set_streamlit_options()
load_css("webapp/style.css")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Generate or retrieve session ID
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())  # Generate a unique ID

# Get the current timestamp
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Log the user session with a print statement
user_id = st.session_state["user_id"]
print(f"[{timestamp}] New user session: {user_id} (Forside)")

if "df_pl" not in st.session_state:
    with st.spinner("Klargør side..."):
        df_retrieved = get_data()

        encoded_key = os.getenv("ENCRYPTION_KEY")

        if encoded_key is None:
            raise ValueError("ENCRYPTION_KEY is not set in the environment variables.")

        encryption_key = base64.b64decode(encoded_key)

        col_list = ["Område", "ISIN kode", "Værdipapirets navn"]
        st.session_state.df_pl = decrypt_dataframe(df_retrieved, encryption_key, col_list)

st.logo("webapp/images/GC_png_oneline_lockup_Outline_Blaa_RGB.png")

# Title of the app
st.title("Kommunernes og regionernes investeringer")
st.markdown(
    """ 
    **Hvis der anvendes data fra denne database i et journalistisk produkt eller i en anden sammenhæng, skal Gravercentret og Danwatch nævnes som kilde.** 
    **F.eks.: ”Det viser data, som er indsamlet og bearbejdet af Gravercentret, Danmarks Center for Undersøgende Journalistik, i samarbejde med Danwatch."**
            """
)
st.markdown(
    """
            Gravercentret, Danmarks Center for Undersøgende Journalistik, har sammen med Danwatch undersøgt, hvilke værdipapirer de danske kommuner og regioner har valgt at investere i. \n
            Vi har kortlagt, hvilke værdipapirer der ligger nede i de investeringsfonde og investeringsforeninger, som kommunerne og regionerne har sat deres penge i.\n
            Disse oplysninger har vi sammenholdt med lister over hvilke værdipapirer, der er sortlistet af danske banker og pensionsselskaber samt FN. \n
            Herunder kan du se oplysninger fra alle kommuner og regioner – og du kan downloade oplysningerne i Excel-format.\n
            I den lyseblå kollonne til venstre kan du søge i data.
            """
)
with st.expander("🟥🟧🟨 - Læs mere: Hvordan skal tallene forstås?", icon="❔"):
    st.markdown(
        """
                I tabellen nedenfor finder du informationer om samtlige værdipapirer danske kommuner og regioner havde investeret i i sommeren 2024. \n
                For hvert værdipapir er det angivet, hvilken kommune eller region, der er ejeren, hvad værdipapirets navn er, og hvor meget værdipapiret er værd.\n
                Værdipapirer, der er udpeget som problematiske, har vi markeret med enten en rød, en orange eller en gul firkant.\n
                Altså viser farverne om værdipapiret optræder på en eksklusionsliste over papirer danske banker, pensionsselskaber eller FN **ikke** vil investere i af forskellige etiske årsager.\n
                Vi har opdelt de problematiske værdipapirer i tre kategorier:\n
                - 🟥(1) - **Rød**: Disse værdipapirer er udstedt af problematiske selskaber.
                - 🟧(2) - **Orange**: Disse værdipapirer er udstedet af problematiske lande.
                - 🟨(3) - **Gul**: Disse værdipapirer er potentielt kontroversielle.\n
                For hvert værdipapir, der er markeret som problematisk, er der i tabellens kollonne "Eksklusion (Af hvem og hvorfor)" en forklaring på, hvem der har udpeget det som problematisk, og hvad årsagen er.\n
                I tabellen kan du også se, hvilken type værdipapiret er (f.eks. aktie eller obligation), værdipapirets ISIN-nummer (et unikt nummer ligesom et CPR-nummer), samt hvem der har udstedt papiret.\n
                Data kan downloades til Excel neden under tabellen.\n
                Læs mere om vores metode i [her](/Sådan_har_vi_gjort).
                """
    )
# Get unique municipalities and sort alphabetically
dropdown_options = get_unique_kommuner(st.session_state.df_pl)

# Get list of categories/reasons
unique_categories_list = get_unique_categories(st.session_state.df_pl)

# Costum choice for dropdown
all_values = "Hele landet"
municipalities = "Alle kommuner"
regions = "Alle regioner"
samsø = "Samsø"
læsø = "Læsø"

# Sidebar with selection options
with st.sidebar:
    user_choice = st.selectbox(
        "Vælg område:",
        dropdown_options,
        help="Skriv i boksen for at søge efter bestemt kommune/region.",
        placeholder="Vælg en kommune/region.",
    )

    selected_categories = st.multiselect(
        "Vælg problemkategori:",
        unique_categories_list,  # Options
        help="Vi har grupperet de mange årsager til eksklusion i hovedkategorier. Vælg én eller flere.",
        placeholder="Vælg problemkategori.",
    )

    search_query = st.text_input("Fritekst søgning i tabellen:", "", help="Søg f.eks. efter et selskabs navn eller et ISIN-nummer.")

    st.markdown("For mere avanceret søgning, brug ['Søg videre'](/Søg_videre).")

    # Filter dataframe based on user's selection
    filtered_df = filter_dataframe_by_choice(st.session_state.df_pl, user_choice)

    filtered_df = filter_df_by_search(filtered_df, search_query)

    filtered_df = filter_dataframe_by_category(filtered_df, selected_categories)

    filtered_df = fix_column_types_and_sort(filtered_df)

    if user_choice in [all_values, municipalities, regions] and search_query or selected_categories:
        if search_query:
            st.markdown(
                f"Antal kommuner/regioner, hvor '{search_query}' indgår: \n **{filtered_df.select(pl.col("Område").n_unique()).to_numpy()[0][0]}**"
            )
        else:
            st.markdown(
                f"Antal kommuner/regioner, der fremgår efter filtrering: \n **{filtered_df.select(pl.col("Område").n_unique()).to_numpy()[0][0]}**"
            )

    write_markdown_sidebar()

# Conditionally display the header based on whether a search query is provided
if selected_categories:
    select_string = ", ".join(selected_categories)
if search_query and not selected_categories:
    st.markdown(f'Data for "{user_choice}" og "{search_query}":')
if selected_categories and not search_query:
    st.subheader(f'Data for "{user_choice}" og "{select_string}":')
if selected_categories and search_query:
    st.subheader(f'Data for "{user_choice}", "{select_string}" og "{search_query}":')
if not selected_categories and not search_query:
    if user_choice == "Hele landet":
        st.markdown(
            f"### Data for alle kommuner og regioner: \n ##### (Vælg en enkelt kommune eller region i panelet til venstre)"
        )
    else:
        st.subheader(f'Data for "{user_choice}":')

# Create three columns
col1, col2 = st.columns([0.4, 0.6])

# Column 1: Pie chart for "Type" based on "Markedsværdi (DKK)"
with col1:
    if filtered_df.shape[0] == 0:
        st.subheader(f"**Der er ingen værdipapirer/investeringer.**")
    else:
        create_pie_chart(filtered_df)

# Column 2: Number of problematic investments
with col2:
    with st.container(border=True):
        header_numbers = "Antal investeringer udpeget som problematiske:"
        st.markdown(
            f'<h4 style="color:black; text-align:center;">{header_numbers}</h4>',
            unsafe_allow_html=True,
        )

        # Count the rows where 'Problematisk ifølge:' is not empty
        problematic_count = filtered_df.filter(filtered_df["Priority"].is_in([2, 3])).shape[0]
        problematic_count = format_number_european(problematic_count)
        st.markdown(
            f'<h2 style="color:black; text-align:center;">{problematic_count}</h2>',
            unsafe_allow_html=True,
        )

        problematic_count_red = filtered_df.filter(filtered_df["Priority"] == 3).shape[0]
        problematic_count_red = format_number_european(problematic_count_red)

        problematic_count_orange = filtered_df.filter(filtered_df["Priority"] == 2).shape[0]
        problematic_count_orange = format_number_european(problematic_count_orange)

        # Using HTML to style text with color
        st.markdown(
            f"<div style='text-align:center;'> Heraf <span style='color:red; font-size:25px;'><b>{problematic_count_red}</b></span> sortlistede værdipapirer fra selskaber, "
            f"og <span style='color:#FE6E34; font-size:25px;'><b>{problematic_count_orange}</b></span> statsobligationer fra sortlistede lande.</div>",
            unsafe_allow_html=True,
        )

        problematic_count_yellow = filtered_df.filter(filtered_df["Priority"] == 1).shape[0]
        problematic_count_yellow = format_number_european(problematic_count_yellow)

        # Using HTML to style text with color
        st.markdown(" ")
        st.markdown(
            f"<div style='text-align:center;'> Derudover er der <span style='color:#FEB342; font-size:20px;'><b>{problematic_count_yellow}</b></span> potentielt problematiske værdipapirer. </div>",
            unsafe_allow_html=True,
        )

    # Nøgletal
    with st.container(border=True):
        st.subheader("Nøgletal")

        # Calculate the total number of investments
        antal_inv = format_number_european(len(filtered_df))

        st.write(f"**Antal investeringer:** {antal_inv}")

        # Calculate the total sum of 'Markedsværdi (DKK)' and display it in both DKK and millions
        total_markedsvaerdi = (
            filtered_df.select(pl.sum("Markedsværdi (DKK)")).to_pandas().iloc[0, 0]
        ).astype(int)

        markedsvaerdi_euro = format_number_european(total_markedsvaerdi)
        markedsvaerdi_euro_short = round_to_million_or_billion(total_markedsvaerdi, 1)
        st.write(
            f"**Total markedsværdi (DKK):** {markedsvaerdi_euro} {markedsvaerdi_euro_short}"
        )

        # Filter for problematic investments and calculate the total sum of their 'Markedsværdi (DKK)'
        prob_df = filtered_df.filter(filtered_df["Priority"].is_in([2, 3]))
        prob_markedsvaerdi = (
            prob_df.select(pl.sum("Markedsværdi (DKK)")).to_pandas().iloc[0, 0]
        ).astype(int)

        prob_markedsvaerdi_euro = format_number_european(prob_markedsvaerdi)
        prob_markedsvaerdi_euro_short = round_to_million_or_billion(prob_markedsvaerdi, 1)
        st.write(
            f"**Markedsværdi af problematiske investeringer (DKK):** {prob_markedsvaerdi_euro} {prob_markedsvaerdi_euro_short}" 
        )

with st.spinner("Henter data.."):

    # Display the dataframe below the three columns
    display_df = filtered_df.with_columns(
        pl.col("Markedsværdi (DKK)")
        .map_elements(format_number_european, return_dtype=pl.Utf8)
        .alias("Markedsværdi (DKK)"),
    )

    st.dataframe(
        display_df[
            [
                # "Index",
                "OBS",
                "Område",
                "Værdipapirets navn",
                "Markedsværdi (DKK)",
                "Eksklusion (Af hvem og hvorfor)",
                "Sortlistet",
                "Problemkategori",
                "Type",
                "ISIN kode",
                "Udsteder",
            ]
        ],
        column_config={
            "OBS": st.column_config.TextColumn(),
            "Område": "Område",
            "Udsteder": st.column_config.TextColumn(width="small"),
            "Markedsværdi (DKK)": "Markedsværdi (DKK)*",  # st.column_config.NumberColumn(format="%.2f"),
            "Type": "Type",
            "Problematisk ifølge:": st.column_config.TextColumn(width="medium"),
            "Eksklusion (Af hvem og hvorfor)": st.column_config.TextColumn(
                width="large",
                help="Nogle banker og pensionsselskaber har oplyst deres eksklusionsårsager på engelsk, hvilket vi har beholdt af præcisionshensyn.",
            ),  # 1200
            "Sortlistet": st.column_config.TextColumn(
                width="small",
                help="Så mange eksklusionslister står værdipapiret på.",
            ), 
            "Udsteder": st.column_config.TextColumn(width="large"),
        },
        hide_index=True,
    )       

# Call the function to display relevant links based on the 'Problematisk ifølge:' column
st.markdown(
    "\\* *Markedsværdien (DKK) er et øjebliksbillede. Tallene er oplyst af kommunerne og regionerne selv ud fra deres senest opgjorte opgørelser.*"
)

generate_organization_links(filtered_df, "Problematisk ifølge:")
st.markdown("**Mere om værdipapirer udpeget af Gravercentret:** [Mulige historier](/Mulige_historier)")

filtered_df = filtered_df.to_pandas()
filtered_df.drop("Priority", axis=1, inplace=True)

# Convert dataframe to Excel
excel_data = to_excel_function(filtered_df)

# Create a download button
st.download_button(
    label="Download til Excel",
    data=excel_data,
    file_name=f"Investeringer for {user_choice}{search_query}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

if user_choice not in [all_values, municipalities, regions, samsø, læsø]:
    st.subheader(f"Eksklusionsårsager for investeringer foretaget af {user_choice}: ")

    st.info(
        """Listen nedenfor er genereret med kunstig intelligens, og der tages derfor forbehold for fejl.
        Nedenstående liste er muligvis ikke udtømmende.""",
        icon="ℹ️",
    )
    st.markdown("OBS: Teksterne er ved at blive rettet til. ")
    ai_text = get_ai_text(user_choice)

    st.markdown(ai_text)

import time
from datetime import timedelta, datetime

import streamlit as st
from streamlit_cookies_controller import CookieController


controller = CookieController(key="newsletter_popup")


def _close_popup():
    expire_at = datetime.now() + timedelta(days=30)
    controller.set("newsletter_popup_closed", "true", expires=expire_at)


def newsletter_popup():
    closed = controller.get("newsletter_popup_closed")
    if closed == "true":
        return

    container = st.container(
        width=500,
        border=True,
    )
    with container:
        col1, col2 = st.columns(2)
        with col1:
            st.image("images/newsletter.png")
        with col2:
            st.markdown(
                """
                ### Tilmeld dig Gravercentrets nyhedsbrev
                Få inspiration, tips, viden og researchpakker og læs, hvordan vi hjælper medier.

                Vi udsender nyhedsbrevet nogle få gange hver måned. Du kan altid afmelde det igen.
                """
            )
        with st.container(horizontal=True):
            st.link_button("Tilmeld nyhedsbrev", url="https://gravercentret.dk/nyhedsbrev/")
            close = st.button("Luk", on_click=_close_popup)

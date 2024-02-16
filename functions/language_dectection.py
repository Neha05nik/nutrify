from lingua import Language, LanguageDetectorBuilder
import streamlit as st

@st.cache_resource()
def language_initialization():
    # Languages we want to detect
    languages = [Language.ENGLISH, Language.FRENCH, Language.GERMAN, Language.SPANISH, Language.DANISH, Language.ITALIAN]
    
    # We build the detector object
    #detector = LanguageDetectorBuilder.from_all_spoken_languages()\
    detector = LanguageDetectorBuilder.from_languages(*languages)\
    .with_minimum_relative_distance(0.9)\
    .build()

    return detector

def detect_language(sentence):
    """
    Argument: sentence to recognize the language
    Return: Detected language
    """
    detector = language_initialization()
    
    detected_language = detector.detect_language_of(sentence)
    
    if detected_language:
        return str(detected_language)[9:]
    
    # By default, we return english
    
    else:
        return "English"
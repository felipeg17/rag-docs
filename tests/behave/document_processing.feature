Feature: DocumentProcessing
    As a rag-docs user,
    I want to ensure that document processing functionality of the backend works correclty,
    so we can verify that a pdf document is ingested in the vector databse and it is
    retrivable as expected.

    Scenario:
        Given the vector database is running
        And the backend is running
        When a pdf document with title "ros-intro" is uploaded
        Then document with title "ros-intro" is created in the vector database
        And the document with title "ros-intro" is retrivable from the vector database
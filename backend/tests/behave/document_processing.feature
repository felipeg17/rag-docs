Feature: DocumentProcessing
    As a rag-docs user,
    I want to ensure that document processing functionality of the backend works correctly,
    so we can verify that a pdf document is ingested, then persistent records are created in
    the persistent storage and in the vector database and both are retrievable as expected.

    Scenario:
        Given the persistent database is running
        And the vector database is running
        And the backend is running
        When a pdf document with title "ros-intro" is uploaded
        Then a document record is created in the persistent database
        And document with title "ros-intro" is created in the vector database
        And the document record should be retrivable from the persistent database
        And the document with title "ros-intro" should be retrievable from the vector database


    Scenario:
        Given the persistent database is running
        And the vector database is running
        And the backend is running
        When a pdf document with title "ros-intro" is uploaded
        Then the document record should be retrivable from the persistent database
        And the document with title "ros-intro" should be retrievable from the vector database
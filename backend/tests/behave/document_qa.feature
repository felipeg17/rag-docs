Feature: DocumentQa
    As a rag-docs user,
    I want to ensure that qa functionality of the backend works correctly,
    so we can verify that a pdf document is ingested in the vector database, then we
    can get answer using the rag service and the interaction is recorded

    Scenario:
        Given the persistent database is running
        And the vector database is running
        And the backend is running
        When a pdf document with title "ros-intro" is uploaded
        And a question about the document is made
        Then an interaction record is created in the persistent database
        And document with title "ros-intro" is created in the vector database
        And the document with title "ros-intro" should be retrievable from the vector database
        And a question is answered using the document with title "ros-intro" chunks as reference
        And the interaction record attached to the document should be retrievable from the persistent database
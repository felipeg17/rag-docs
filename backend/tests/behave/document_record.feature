Feature: Create a document record
    As a rag-docs user,
    I want to ensure that the document creation in the persistent database works
    correctly.

    Scenario:
        Given the persistent database is running
        When a record of the document with title "test-document" is created in the persistent database
        Then the document record should be retrievable from the persistent database
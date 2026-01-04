Feature: mcodex smoke

  Scenario: Create a text with authors from config
    Given an empty mcodex config
    When I run "mcodex author add Novy \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Článek o něčem\" --author=Novy"
    Then a text directory "text_clanek_o_necem" exists
    And a file "text_clanek_o_necem/text.md" exists
    And a file "text_clanek_o_necem/todo.md" exists
    And a file "text_clanek_o_necem/checklist.md" exists
    And a directory "text_clanek_o_necem/.snapshot" exists
    And a file "text_clanek_o_necem/.snapshot/.gitkeep" exists
    And the metadata in "text_clanek_o_necem" contains author "Novy"

  Scenario: Add and remove author on an existing text
    Given an empty mcodex config
    When I run "mcodex author add eva \"Eva Marie\" \"Svobodová\" eva@example.com"
    And I run "mcodex author add Novy \"Jan\" \"Novák\" jan.novak@example.com"
    And I run "mcodex create \"Text\" --author=eva"
    And I run "mcodex text author add \"text_text\" Novy"
    Then the metadata in "text_text" contains author "Novy"
    When I run "mcodex text author remove \"text_text\" Novy"
    Then the metadata in "text_text" does not contain author "Novy"


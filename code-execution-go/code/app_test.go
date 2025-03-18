package code

import (
	"reflect"
	"testing"
)

func TestAListWithOneObjectNeedsToBeUpdatedImageIDToMatchBList(t *testing.T) {
	listA := []map[string]interface{}{{"is_main": true, "order": 1, "image_id": 10}}
	listB := []map[string]interface{}{{"is_main": true, "order": 1, "image_id": 20}}
	expectedOutput := []map[string]interface{}{{"action": "update", "image_id": 20, "order": 1}}

	result := GetChanges(listA, listB)

	if !reflect.DeepEqual(result, expectedOutput) {
		t.Errorf("Expected %v, but got %v", expectedOutput, result)
	}
}

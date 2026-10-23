// SPDX-License-Identifier: GPL-3.0-or-later
// Additional product regressions, not translated Blender cases.
use blended_core::priority_heaps::{MinHeap, SimpleMinHeap};

#[test]
fn priority_changes_preserve_handle_payload_association() {
    let mut heap = MinHeap::new();
    let first = heap.insert(2.0, 10);
    let second = heap.insert(4.0, 20);
    heap.update(second, 1.0);
    assert_eq!(heap.node_value(second), 1.0);
    assert_eq!(heap.top(), second);
    assert_eq!(heap.pop_min(), 20);
    heap.update(first, 7.0);
    assert_eq!(heap.node_value(first), 7.0);
    assert_eq!(heap.pop_min(), 10);
    assert!(heap.is_empty());
}

#[test]
fn handle_and_simple_heaps_retain_distinct_equal_key_policies() {
    let mut handles = MinHeap::new();
    let mut simple = SimpleMinHeap::new();
    for payload in [10, 20, 30] {
        handles.insert(1.0, payload);
        simple.insert(1.0, payload);
    }
    assert_eq!(handles.pop_min(), 30);
    assert_eq!(simple.pop_min(), 10);
}

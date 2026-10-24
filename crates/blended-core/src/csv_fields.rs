// SPDX-FileCopyrightText: 2025 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Byte-oriented Rust adaptation of pinned BLI_csv_parse.hh / csv_parse.cc.
// Parallel native scheduling and the arena allocator are not reproduced.
use std::borrow::Cow;

#[derive(Debug, Clone)]
pub struct Options {
    pub delimiter: u8,
    pub quote: u8,
    pub quote_escape_chars: Vec<u8>,
    pub chunk_size_bytes: i64,
}
impl Default for Options {
    fn default() -> Self { Self { delimiter: b',', quote: b'"', quote_escape_chars: vec![b'"', b'\\'], chunk_size_bytes: 64 * 1024 } }
}
pub type Fields<'a> = Vec<&'a [u8]>;
pub type Records<'a> = Vec<Fields<'a>>;

pub fn find_end_of_simple_field(buffer: &[u8], start: usize, delimiter: u8) -> usize {
    let mut i = start;
    while i < buffer.len() {
        if buffer[i] == delimiter || buffer[i] == b'\n' || buffer[i] == b'\r' { return i; }
        i += 1;
    }
    buffer.len()
}
pub fn find_end_of_quoted_field(buffer: &[u8], start: usize, quote: u8, escape: &[u8]) -> Option<usize> {
    let mut i = start;
    while i < buffer.len() {
        if escape.contains(&buffer[i]) && i + 1 < buffer.len() && buffer[i + 1] == quote { i += 2; continue; }
        if buffer[i] == quote { return Some(i); }
        i += 1;
    }
    None
}
fn trailing_delimiter<'a>(buffer: &'a [u8], i: usize, fields: &mut Fields<'a>) {
    if i == buffer.len() || (i < buffer.len() && matches!(buffer[i], b'\n' | b'\r')) { fields.push(&[]); }
}
/// Parse one record and retain raw borrowed field bytes, including escapes.
/// Quoted-field suffix handling follows the pinned parser, not a stricter RFC parser.
pub fn parse_record_fields<'a>(buffer: &'a [u8], start: usize, options: &Options) -> Option<(usize, Fields<'a>)> {
    let mut fields = Vec::new(); let mut i = start;
    while i < buffer.len() {
        let c = buffer[i];
        if c == b'\n' { return Some((i + 1, fields)); }
        if c == b'\r' { i += 1; continue; }
        if c == options.delimiter {
            fields.push(&buffer[i..i]); i += 1; trailing_delimiter(buffer, i, &mut fields); continue;
        }
        if c == options.quote {
            i += 1;
            let end = find_end_of_quoted_field(buffer, i, options.quote, &options.quote_escape_chars)?;
            fields.push(&buffer[i..end]); i = end;
            while i < buffer.len() {
                let c = buffer[i];
                if c == options.quote { i += 1; continue; }
                if c == options.delimiter { i += 1; trailing_delimiter(buffer, i, &mut fields); break; }
                if matches!(c, b'\n' | b'\r') { break; }
                i += 1;
            }
            continue;
        }
        let end = find_end_of_simple_field(buffer, i, options.delimiter);
        fields.push(&buffer[i..end]); i = end;
        if i < buffer.len() && buffer[i] == options.delimiter { i += 1; trailing_delimiter(buffer, i, &mut fields); }
    }
    Some((buffer.len(), fields))
}
fn parse_records<'a>(buffer: &'a [u8], options: &Options) -> Option<Records<'a>> {
    let mut start = 0; let mut records = Vec::new();
    while start < buffer.len() {
        let (end, fields) = parse_record_fields(buffer, start, options)?;
        assert!(end > start, "Parser must advance");
        if !fields.is_empty() { records.push(fields); }
        start = end;
    }
    Some(records)
}
fn next_record_guess(buffer: &[u8], start: usize) -> usize {
    buffer[start..].iter().position(|&c| c == b'\n').map_or(buffer.len(), |offset| start + offset + 1)
}
/// Retain chunk boundaries and whole-data retry for a malformed split. Callbacks
/// execute sequentially; they can run twice on a retry, as the original contract allows.
pub fn parse_csv_in_chunks<'a, T>(buffer: &'a [u8], options: &Options, mut header: impl FnMut(&[&'a [u8]]), mut process: impl FnMut(&Records<'a>) -> T) -> Option<Vec<T>> {
    let (data_start, fields) = parse_record_fields(buffer, 0, options)?;
    header(&fields);
    let data = &buffer[data_start..]; let mut start = 0; let mut results = Vec::new();
    let size = options.chunk_size_bytes.max(1) as usize;
    while start < data.len() {
        let guess = start.saturating_add(size).min(data.len());
        let end = next_record_guess(data, guess);
        if let Some(records) = parse_records(&data[start..end], options) { results.push(process(&records)); }
        else {
            let records = parse_records(data, options)?;
            results.clear(); results.push(process(&records)); return Some(results);
        }
        start = end;
    }
    Some(results)
}
pub fn unescape_field<'a>(source: &'a [u8], options: &Options) -> Cow<'a, [u8]> {
    if !source.iter().any(|c| options.quote_escape_chars.contains(c)) { return Cow::Borrowed(source); }
    let mut output = Vec::with_capacity(source.len()); let mut i = 0;
    while i < source.len() {
        if options.quote_escape_chars.contains(&source[i]) && i + 1 < source.len() && source[i + 1] == options.quote {
            output.push(options.quote); i += 2;
        } else { output.push(source[i]); i += 1; }
    }
    Cow::Owned(output)
}

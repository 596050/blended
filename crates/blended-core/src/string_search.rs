// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Adapted from pinned BLI string_search.cc, 94363991e7dcf39e2d70614aa002ab6f67764a5d.
// Covers tested distance, fuzzy-error and word-normalisation routines; not the
// complete Search/initials-ranking subsystem or arbitrary locale case-folding.
use crate::string_ops::utf8_step;
fn codepoints(s:&[u8])->Vec<u32>{let mut out=Vec::new();let mut i=0;while i<s.len(){let(c,n)=utf8_step(s,i);out.push(c);i+=n;}out}
fn distance(a:&[u32],b:&[u32])->i32{
    assert!(a.len()<i32::MAX as usize && b.len()<i32::MAX as usize);
    let mut v0=vec![0;b.len()+1];let mut v1:Vec<i32>=(0..=b.len() as i32).collect();let mut v2=vec![0;b.len()+1];
    for i in 0..a.len(){v2[0]=(i+1) as i32;
        for j in 0..b.len(){let mut cost=(v1[j+1]+1).min(v2[j]+1).min(v1[j]+i32::from(a[i]!=b[j]));
            if i>0&&j>0&&a[i]==b[j-1]&&a[i-1]==b[j]{cost=cost.min(v0[j-1]+1);}v2[j+1]=cost;}
        core::mem::swap(&mut v0,&mut v1);core::mem::swap(&mut v1,&mut v2);
    }
    v1[b.len()]
}
pub fn damerau_levenshtein_distance(a:&[u8],b:&[u8])->i32{distance(&codepoints(a),&codepoints(b))}
pub fn fuzzy_errors(query:&[u8],full:&[u8])->i32{
    if query.is_empty()||full.windows(query.len()).any(|v|v==query){return 0;}
    let q=codepoints(query);let f=codepoints(full);if q.len()==1{return -1;}
    let max_errors=q.len()/8+1;if q.len()>f.len()+max_errors{return -1;}
    let width=(q.len()+max_errors).min(f.len());let acceptable=max_errors+width.saturating_sub(q.len());let mut start=0;
    loop{
        let mut d=0;
        if start<f.len()&&(f[start]==q[0]||f[start]==q[1]){d=distance(&q,&f[start..start+width]);if d as usize<=acceptable{return d;}}
        if start+width==f.len(){return -1;}start+=(1.max(d as usize/2)).min(f.len()-start-width);
    }
}
pub fn normalized_words(text:&[u8])->(Vec<Vec<u8>>,Vec<i32>){
    let lower:Vec<u8>=text.iter().map(u8::to_ascii_lowercase).collect();let mut words=Vec::new();let mut ids=Vec::new();let mut start=None;let mut i=0;let mut group=0;
    while i<text.len(){let(c,n)=utf8_step(text,i);let separator=matches!(c,32|45|95|47|0x25b8);
        if separator{if let Some(s)=start.take(){words.push(lower[s..i].to_vec());ids.push(group);}}else if start.is_none(){start=Some(i);}
        if c==0x25b8{group+=1;}i+=n;
    }
    if let Some(s)=start{words.push(lower[s..].to_vec());ids.push(group);}(words,ids)
}

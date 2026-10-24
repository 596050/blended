// SPDX-FileCopyrightText: 2023 Blender Authors
// SPDX-License-Identifier: GPL-2.0-or-later
// Adapted from pinned string.cc, string_utils.cc and string_utf8.cc.
// Reference: 94363991e7dcf39e2d70614aa002ab6f67764a5d.
// Byte slices preserve C-string boundaries without claiming native allocation
// layout or non-C-locale equivalence. Invalid bounds fail rather than invoking UB.
pub fn c_string(bytes:&[u8])->&[u8] {
    &bytes[..bytes.iter().position(|&c|c==0).unwrap_or(bytes.len())]
}
pub fn nlen(bytes:&[u8],max:usize)->usize {c_string(&bytes[..bytes.len().min(max)]).len()}
pub fn copy_into(dst:&mut[u8],src:&[u8],capacity:usize)->usize {
    assert!(capacity>0 && capacity<=dst.len(),"Invalid C-string destination capacity");
    let src=c_string(src);let n=src.len().min(capacity-1);
    dst[..n].copy_from_slice(&src[..n]);dst[n]=0;n
}
pub fn buffer(initial:&[u8],capacity:usize)->Vec<u8>{let mut dst=vec![0;capacity];copy_into(&mut dst,initial,capacity);dst}
pub fn ncat(dst:&mut[u8],src:&[u8],capacity:usize) {
    assert!(capacity>0 && capacity<=dst.len());let used=nlen(dst,capacity);
    assert!(used<capacity,"Unterminated destination");
    copy_into(&mut dst[used..],src,capacity-used);
}
pub fn replace_range(dst:&mut[u8],start:usize,end:usize,replacement:&[u8]) {
    let value=c_string(dst);assert!(start<=end && end<=value.len());
    let mut combined=Vec::with_capacity(value.len().saturating_add(replacement.len()));
    combined.extend_from_slice(&value[..start]);combined.extend_from_slice(c_string(replacement));combined.extend_from_slice(&value[end..]);
    let capacity=dst.len();copy_into(dst,&combined,capacity);
}
pub fn strncmp(a:&[u8],b:&[u8],count:usize)->i32 {
    for i in 0..count {let x=*a.get(i).unwrap_or(&0);let y=*b.get(i).unwrap_or(&0);if x!=y{return i32::from(x)-i32::from(y);}if x==0{break;}}
    0
}
pub fn starts_with(s:&[u8],prefix:&[u8])->bool{c_string(s).starts_with(c_string(prefix))}
pub fn ends_with(s:&[u8],suffix:&[u8])->bool{c_string(s).ends_with(c_string(suffix))}
pub fn is_decimal(s:&[u8])->bool{let s=c_string(s);!s.is_empty()&&s.iter().all(u8::is_ascii_digit)}
pub fn max_possible_words(n:usize)->usize{n/2+1}
pub fn element_in_delimited(text:&[u8],delimiter:u8,element:&[u8])->bool{c_string(text).split(|&c|c==delimiter).any(|s|s==c_string(element))}
pub fn ncasestr(text:&[u8],find:&[u8],len:usize)->*const u8 {
    let hay=c_string(text);let needle=c_string(find);
    if needle.is_empty(){return text.as_ptr();}
    // The original len is the needle comparison length, not a haystack bound.
    // A nonempty needle with len==0 still searches its first byte.
    for i in 0..hay.len(){
        if hay[i].to_ascii_lowercase()!=needle[0].to_ascii_lowercase(){continue;}
        let mut matched=true;
        for j in 1..len {
            let a=hay.get(i+j).copied().unwrap_or(0).to_ascii_lowercase();
            let b=needle.get(j).copied().unwrap_or(0).to_ascii_lowercase();
            if a!=b{matched=false;break;}if a==0{break;}
        }
        if matched{return text.as_ptr().wrapping_add(i);}
    }
    core::ptr::null()
}
pub fn join_owned(parts:&[&[u8]],separator:Option<u8>)->Vec<u8> {
    let mut out=Vec::new();for (i,p) in parts.iter().enumerate(){if i!=0{if let Some(c)=separator{out.push(c);}}out.extend_from_slice(c_string(p));}out
}
pub fn join_into(dst:&mut[u8],capacity:usize,parts:&[&[u8]],separator:Option<u8>)->usize {
    assert!(capacity>0&&capacity<=dst.len());let mut used=0;
    for (i,p) in parts.iter().enumerate(){
        if i>0{if let Some(c)=separator{if used==capacity-1{break;}dst[used]=c;used+=1;}}
        for &c in c_string(p){if used==capacity-1{dst[used]=0;return used;}dst[used]=c;used+=1;}
    }
    dst[used]=0;used
}
pub fn find_split_words(text:&[u8],max_length:usize,delimiter:u8,words:&mut[[i32;2]],max_words:usize)->usize {
    assert!(max_words<=words.len());let text=c_string(&text[..text.len().min(max_length)]);assert!(text.len()<=i32::MAX as usize);
    let mut n=0;let mut i=0;
    while i<text.len()&&n<max_words{
        while i<text.len()&&text[i]==delimiter{i+=1;}
        if i==text.len(){break;}let start=i;
        while i<text.len()&&text[i]!=delimiter{i+=1;}
        words[n]=[start as i32,(i-start) as i32];n+=1;
    }
    n
}

/// UTF-8 decoding for the valid Unicode inputs covered by the pinned tests.
/// Invalid sequences consume one byte as a safe adapter policy. Invalid-byte
/// return values and obsolete five/six-byte, surrogate or overlong encodings
/// are outside this port's verified compatibility scope.
pub fn utf8_step(bytes:&[u8],offset:usize)->(u32,usize) {
    let first=bytes[offset];if first<0x80{return(first as u32,1);}
    let n=match first{0xc2..=0xdf=>2,0xe0..=0xef=>3,0xf0..=0xf4=>4,_=>return(first as u32,1)};
    if offset+n<=bytes.len(){if let Ok(s)=core::str::from_utf8(&bytes[offset..offset+n]){return(s.chars().next().unwrap() as u32,n);}}
    (first as u32,1)
}
pub struct Partition<'a>{pub prefix_len:usize,text:&'a[u8],separator:Option<usize>,suffix:Option<usize>}
impl Partition<'_>{
    pub fn separator_ptr(&self)->*const u8{self.separator.map_or(core::ptr::null(),|i|self.text.as_ptr().wrapping_add(i))}
    pub fn suffix_ptr(&self)->*const u8{self.suffix.map_or(core::ptr::null(),|i|self.text.as_ptr().wrapping_add(i))}
    pub fn suffix_bytes(&self)->Option<&[u8]>{self.suffix.map(|i|c_string(&self.text[i..]))}
}
pub fn partition<'a>(text:&'a[u8],limit:Option<usize>,delimiters:&[u32],utf8:bool,right:bool)->Partition<'a>{
    let end=limit.unwrap_or_else(||c_string(text).len());assert!(end<=text.len());
    let mut positions=Vec::new();let mut i=0;
    while i<end && (right||text[i]!=0){let(c,n)=if utf8{utf8_step(&text[..end],i)}else{(text[i] as u32,1)};positions.push((i,c,n));i+=n;}
    let matches=|&(i,c,_):&(usize,u32,usize)|(!utf8||!right||i>0)&&delimiters.iter().take_while(|&&d|d!=0).any(|&d|d==c);
    // Pinned UTF-8 right-partition does not inspect the first codepoint.
    // Retain that observable boundary behaviour instead of silently correcting it.
    let selected=if right{positions.iter().rev().find(|p|matches(p))}else{positions.iter().find(|p|matches(p))};
    if let Some(&(i,_,n))=selected{Partition{prefix_len:i,text,separator:Some(i),suffix:Some(i+n)}}
    else{Partition{prefix_len:end,text,separator:None,suffix:None}}
}

fn write_format(dst:&mut[u8],text:String){let n=dst.len();copy_into(dst,text.as_bytes(),n);}
fn grouped(digits:&str)->String {
    let (sign,d)=digits.strip_prefix('-').map_or(("",digits),|v|("-",v));let mut out=String::from(sign);
    for(i,c)in d.chars().enumerate(){if i>0&&(d.len()-i)%3==0{out.push(',');}out.push(c);}out
}
pub fn format_i32(dst:&mut[u8],n:i32){write_format(dst,grouped(&n.to_string()));}
pub fn format_u64(dst:&mut[u8],n:u64){write_format(dst,grouped(&n.to_string()));}
pub fn format_bytes(dst:&mut[u8],n:i64,base10:bool){
    let base=if base10{1000.0}else{1024.0};let mut value=n as f64;let mut order:usize=0;
    while value.abs()>=base&&order<5{value/=base;order+=1;}
    let mut text=format!("{:.*}",order.saturating_sub(1),value);
    if let Some(dot)=text.find('.') {while text.len()>dot+2&&text.ends_with('0'){text.pop();}}
    let units=if base10{["B","KB","MB","GB","TB","PB"]}else{["B","KiB","MiB","GiB","TiB","PiB"]};
    text.push(' ');text.push_str(units[order]);write_format(dst,text);
}
pub fn format_decimal(dst:&mut[u8],n:i32){
    let mut value=n as f32;let mut order=0;
    while value.abs()>=1000.0&&order<3{value/=1000.0;order+=1;}
    let decimals=usize::from(order>0&&value.abs()<100.0);
    write_format(dst,format!("{:.*}{}",decimals,value as f64,["","K","M","B"][order]));
}
pub fn format_integer(dst:&mut[u8],n:i32){
    let mut value=n as f32;let mut order=0;
    while value.abs()>=1000.0&&order<3{value/=1000.0;order+=1;}
    let dot=(n as i64).abs()>99999&&value.abs()>99.0;
    if dot{value/=100.0;order+=1;}
    write_format(dst,format!("{}{}{}{}",if n<0{"-"}else{""},if dot{"."}else{""},value.abs().floor() as i32,["","K","M","B"][order]));
}

pub fn escape_into(dst:&mut[u8],src:&[u8],capacity:usize)->usize {
    assert!(capacity>0&&capacity<=dst.len());let mut used=0;
    for &c in src {
        let escaped=match c{b'\\'=>Some(b'\\'),b'"'=>Some(b'"'),9=>Some(b't'),10=>Some(b'n'),13=>Some(b'r'),7=>Some(b'a'),8=>Some(b'b'),12=>Some(b'f'),_=>None};
        let n=if escaped.is_some(){2}else{1};
        // Always reserve a NUL byte. Native calls that write the terminator past
        // their allocation are undefined and not reproduced by safe Rust.
        if used+n>=capacity{break;}
        if let Some(v)=escaped{dst[used]=b'\\';dst[used+1]=v;}else{dst[used]=c;}used+=n;
    }
    dst[used]=0;used
}
pub fn unescape_into(dst:&mut[u8],src:&[u8],maxsrc:usize)->usize {
    let mut i=0;let mut used=0;assert!(!dst.is_empty());
    while i<maxsrc&&i<src.len()&&src[i]!=0{
        let mut c=src[i];
        if c==b'\\'{if let Some(&next)=src.get(i+1){let d=match next{b'"'=>Some(b'"'),b'\\'=>Some(b'\\'),b't'=>Some(9),b'n'=>Some(10),b'r'=>Some(13),b'a'=>Some(7),b'b'=>Some(8),b'f'=>Some(12),_=>None};if let Some(v)=d{c=v;i+=1;}}}
        assert!(used+1<dst.len(),"Insufficient unescape output buffer");dst[used]=c;used+=1;i+=1;
    }
    dst[used]=0;used
}
fn byte_at(s:&[u8],i:usize)->u8{s.get(i).copied().unwrap_or(0)}
fn number_compare(a:&[u8],b:&[u8],tie:&mut i32)->i32{
    let mut za=0;let mut zb=0;while byte_at(a,za)==b'0'{za+=1;}while byte_at(b,zb)==b'0'{zb+=1;}
    let mut n=0;
    loop{let x=byte_at(a,za+n).is_ascii_digit();let y=byte_at(b,zb+n).is_ascii_digit();if x&&y{n+=1;continue;}if x{return 1;}if y{return -1;}break;}
    let result=strncmp(&a[za..],&b[zb..],n);if result!=0{return result;}
    if *tie==0{if za>zb{*tie=1;}else if za<zb{*tie=-1;}}
    0
}
pub fn casecmp_natural(a:&[u8],b:&[u8])->i32{
    let a=c_string(a);let b=c_string(b);let(mut x,mut y,mut tie)=(0,0,0);
    loop{
        if byte_at(a,x).is_ascii_digit()&&byte_at(b,y).is_ascii_digit(){let r=number_compare(&a[x..],&b[y..],&mut tie);if r!=0{return r;}while byte_at(a,x).is_ascii_digit(){x+=1;}while byte_at(b,y).is_ascii_digit(){y+=1;}}
        let c=byte_at(a,x);let d=byte_at(b,y);if c==0||d==0{break;}
        let c=c.to_ascii_lowercase();let d=d.to_ascii_lowercase();
        if c!=d{if c==b'.'{return -1;}if d==b'.'{return 1;}return if(c as i8)<(d as i8){-1}else{1};}
        x+=1;y+=1;
    }
    if tie!=0{tie}else{strncmp(a,b,a.len().max(b.len())+1)}
}
pub fn replace_all(text:&mut Vec<u8>,needle:&[u8],other:&[u8]){
    assert!(!needle.is_empty(),"Empty replacement needle has no terminating original contract");let mut i=0;
    while i<=text.len(){let found=text[i..].windows(needle.len()).position(|w|w==needle);let Some(relative)=found else{break};let start=i+relative;text.splice(start..start+needle.len(),other.iter().copied());i=start+other.len();}
}
fn split_number(name:&[u8],delimiter:u8)->(&[u8],i32){
    if let Some(i)=name.iter().rposition(|&c|c==delimiter){let suffix=&name[i+1..];if !suffix.is_empty()&&suffix.iter().all(u8::is_ascii_digit){if let Ok(text)=core::str::from_utf8(suffix){if let Ok(number)=text.parse::<i32>(){return(&name[..i],number);}}}}
    (name,0)
}
fn suffix(number:i32,delimiter:u8)->Vec<u8>{let mut s=vec![delimiter];s.extend_from_slice(format!("{number:03}").as_bytes());s}
fn utf8_prefix(s:&[u8],max:usize)->&[u8]{let mut i=0;while i<s.len(){let(_,n)=utf8_step(s,i);if i+n>max{break;}i+=n;}&s[..i]}
pub fn unique_name<F:Fn(&[u8])->bool>(exists:&F,delimiter:u8,name:&[u8])->Vec<u8>{
    let name=c_string(name);if !exists(name){return name.to_vec();}let(base,mut number)=split_number(name,delimiter);
    loop{number=number.checked_add(1).expect("Original numeric suffix overflows i32");let mut candidate=base.to_vec();candidate.extend(suffix(number,delimiter));if !exists(&candidate){return candidate;}}
}
pub fn unique_name_into<F:Fn(&[u8])->bool>(exists:&F,default:&[u8],delimiter:u8,name:&mut[u8]){
    assert!(!name.is_empty());let capacity=name.len();
    if name[0]==0{copy_into(name,utf8_prefix(c_string(default),capacity-1),capacity);}
    let original=c_string(name).to_vec();if !exists(&original){return;}let(base,mut number)=split_number(&original,delimiter);
    loop{
        number=number.checked_add(1).expect("Original numeric suffix overflows i32");let suffix=suffix(number,delimiter);
        let mut candidate=if base.is_empty()||suffix.len()+1>=capacity{suffix[..suffix.len().min(capacity-1)].to_vec()}else{let mut c=utf8_prefix(base,capacity-suffix.len()-1).to_vec();c.extend_from_slice(&suffix);c};
        if !exists(&candidate){copy_into(name,&candidate,capacity);return;}
        // Like the original API the callback must eventually accept a candidate.
        candidate.clear();
    }
}

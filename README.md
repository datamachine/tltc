# Telgram API

## Download
The current version of the Telgram API can be found on there site at https://core.telegram.org/schema

## Schema

The schema uses a language named TL to describe the api calls.

For example:

```
boolFalse#bc799737 = Bool;
boolTrue#997275b5 = Bool;

vector#1cb5c415 {t:Type} # [ t ] = Vector t;

error#c4b9f9bb code:int text:string = Error;
```

## combinators

These define the 'combinators' that make up the API. 

In the data communication, a combinator is a sequence of bytes that represents API calls and object data.

It is possible to translate the combinator definitions into fromt he TL schema into types and functions in a language of your choice (e.g. Python).

The basic format of the combinator is:

```
[full combinator identifer] [{optional parameters}|...] [parameters|...] = [result type]
```

###For example:

```
inputPhoneContact#f392b7f4 client_id:long phone:string first_name:string last_name:string = InputContact;
```

"inputPhoneContact#f392b7f4": is the full combinator identifer

"client_id:long", "phone:string", "first_name:string", "last_name:string": are the mandatory parameters

"InputContact": is the result type (what the combinator is ultimately building/returning)

Writing a python function to match this would look something like:

```
def inputPhoneContact(client_id, phone, first_name, last_name)
	return InputContact(client_id, phone, first_name, last_name)
```

###Another example:

```
invokeAfterMsg#cb9f372d {X:Type} msg_id:long query:!X = X;
```

"invokeAfterMsg#cb9f372d": is the full identifer

"{X:Type}": is an optional parameter

"msg_id:long", "query:!X": are the mandatory parameters

"InputContact": is the result type

Writing a python function to match this would look (very roughly) like:

```
def callback_function():
	print('callback done')

def invokeAfterMsg(msg_id, callback, callback_type=None)
	server.send_msg(msg_id).wait()
	callback()
```

### Full Combinator Identifier

The combinators full identifer is broken up as follows

```
[namespace.]<identifer>#<numeric identifer>
```

The namespace and identifer are self explanatory.

The numeric identifer is unique to each combinator as is ultimately derived from the crc32 of the TL combinator string, in hex, and in big endian format.

For example:

```
crc32("boolFalse = Bool") == 0xbc799737
``` 

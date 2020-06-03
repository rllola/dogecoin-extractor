# Dogecoin block chain extractor

Get all the blocks!

Should be wrote in Rust!

## Useful commands

Some useful commands for getting information.

### Get all OP_RETURN message

```
$ cat scripts.txt | grep '^6a'
```

Remove duplicates
```
$ cat scripts.txt | grep '^6a' | sort -u
```

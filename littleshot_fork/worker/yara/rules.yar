rule open_dir
{
    strings:
        $b = "Directory listing for" nocase
        $c = "Index of /"
        $d = "[To Parent Directory]"
        $e = "Directory: /"
    condition:
        $b or $c or $d or $e
}

rule ligma
{
    strings:
        $a = ".exe"

    condition:
        open_dir and $a
}

rule office_titles
{
    strings: 
        $a = "LOGIN TO VIEW DOCUMENT."

    condition:
        $a
}

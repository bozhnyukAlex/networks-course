package main

import (
	"flag"
	"fmt"
	"net"
)

func main() {
	ip := flag.String("ip", "", "target IP address")
	start := flag.Int("start", 1, "start port")
	end := flag.Int("end", 65535, "end port")
	flag.Parse()

	if *ip == "" {
		fmt.Println("Usage: -ip <address> -start <port> -end <port>")
		return
	}

	for port := *start; port <= *end; port++ {
		addr := fmt.Sprintf("%s:%d", *ip, port)
		ln, err := net.Listen("tcp", addr)
		if err != nil {
			continue
		}
		ln.Close()
		fmt.Println(port)
	}
}

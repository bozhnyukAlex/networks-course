package main

import (
	"fmt"
	"net"
)

func main() {
	interfaces, err := net.Interfaces()
	if err != nil {
		fmt.Println("Error:", err)
		return
	}

	for _, iface := range interfaces {
		addrs, err := iface.Addrs()
		if err != nil {
			continue
		}
		for _, addr := range addrs {
			ipnet, ok := addr.(*net.IPNet)
			if !ok {
				continue
			}
			ip := ipnet.IP
			if ip.IsLoopback() || ip.To4() == nil {
				continue
			}

			mask := ipnet.Mask
			fmt.Println("Interface:", iface.Name)
			fmt.Println("IP Address:", ip.String())
			fmt.Println("Network Mask:", net.IP(mask).String())
		}
	}
}

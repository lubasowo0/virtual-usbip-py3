from usbip import Device, Server

class Example(Device):
    strings = {1: "Example", 2: "Device"}

    hid_descriptors = {
        0: [0x5, 0x1, 0x9, 0x2, 0xa1, 0x1, 0x9, 0x1, 0xa1, 0x0, 0x5, 0x9, 0x15, 0x0, 0x25, 0x1, 0x19, 0x1, 0x29, 0x5, 0x75, 0x1, 0x95, 0x5, 0x81, 0x2, 0x95, 0x3, 0x81, 0x1, 0x5, 0x1, 0x16, 0x1, 0x80, 0x26, 0xff, 0x7f, 0x9, 0x30, 0x9, 0x31, 0x75, 0x10, 0x95, 0x2, 0x81, 0x6, 0x15, 0x81, 0x25, 0x7f, 0x9, 0x38, 0x75, 0x8, 0x95, 0x1, 0x81, 0x6, 0x5, 0xc, 0xa, 0x38, 0x2, 0x95, 0x1, 0x81, 0x6, 0xc0, 0xc0],
        1: [0x05, 0x01, 0x09, 0x06, 0xA1, 0x01, 0x05, 0x07, 0x19, 0xE0, 0x29, 0xE7, 0x15, 0x00, 0x25, 0x01, 0x75, 0x01, 0x95, 0x08, 0x81, 0x02, 0x95, 0x01, 0x75, 0x08, 0x81, 0x01, 0x95, 0x05, 0x75, 0x01, 0x05, 0x08, 0x19, 0x01, 0x29, 0x05, 0x91, 0x02, 0x95, 0x01, 0x75, 0x03, 0x91, 0x01, 0x95, 0x06, 0x75, 0x08, 0x15, 0x00, 0x26, 0xFF, 0x00, 0x05, 0x07, 0x19, 0x00, 0x2A, 0xFF, 0x00, 0x81, 0x00, 0xC0],
    }

    descriptor = {
        "bcdUSB": 0x0200,
        "bDeviceClass": 0x0,
        "bDeviceSubClass": 0,
        "bDeviceProtocol": 0,
        "bMaxPacketSize0": 8,
        "idVendor": 0xffff,
        "idProduct": 0x1234,
        "bcdDevice": 0x0101,
        "iManufacturer": 1,
        "iProduct": 2,
        "iSerialNumber": 0,
    }

    configuration = {
        "bNumInterfaces": 2,
        "iConfiguration": 0,
        "bmAttributes": 0xa0,
        "bMaxPower": 50,
    }

    interfaces = [
        [
            {
                "bDescriptorType": 0x4,
                "bInterfaceNumber": 0,
                "bAlternateSetting": 0,
                "bNumEndpoints": 1,
                "bInterfaceClass": 0x03,
                "bInterfaceSubClass": 0x01,
                "bInterfaceProtocol": 0x02,
                "iInterface": 0,
            },
            {
                "bDescriptorType": 0x21,
                "bcdHID": 0x0110,
                "bCountryCode": 0,
                "bNumDescriptors": 1,
                "bDescriptorType2": 0x22,
                "wDescriptorLength": len(hid_descriptors[0]),
            },
            {
                "bDescriptorType": 0x5,
                "bEndpointAddress": 0x81,
                "bmAttributes": 0x03,
                "wMaxPacketSize": 8,
                "bInterval": 4,
            },
        ],
        [
            {
                "bDescriptorType": 0x4,
                "bInterfaceNumber": 1,
                "bAlternateSetting": 0,
                "bNumEndpoints": 1,
                "bInterfaceClass": 0x03,
                "bInterfaceSubClass": 0x00,
                "bInterfaceProtocol": 0x01,
                "iInterface": 0,
            },
            {
                "bDescriptorType": 0x21,
                "bcdHID": 0x0110,
                "bCountryCode": 0,
                "bNumDescriptors": 1,
                "bDescriptorType2": 0x22,
                "wDescriptorLength": len(hid_descriptors[1]),
            },
            {
                "bDescriptorType": 0x5,
                "bEndpointAddress": 0x82,
                "bmAttributes": 0x03,
                "wMaxPacketSize": 16,
                "bInterval": 4,
            },
        ],
    ]



    def handle_control(self, urb):
        print("control on endpoint", urb.ep, "setup", urb.setup)
        #urb.respond(status=0, data=b'')

    def handle_irq(self, urb):
        print("interrupt on endpoint", urb.ep, "direction", "IN" if urb.direction == 1 else "OUT", "data:", urb.data)
        #urb.respond(status=0, data=b'')

    def handle_unlink(self, unlink):
        unlink.respond(unlink.ECONNRESET)


server = Server(Example())
server.run()

"""Constants used in the SCP protocol.
"""
import enum

BOOT_PORT = 54321  # TODO Reference spec
"""Port used to boot a SpiNNaker machine."""

SCP_PORT = 17893  # TODO Reference spec
"""Port used for SDP communication."""

SDP_HEADER_LENGTH = 8  # TODO Reference spec.
"""The number of bytes making up the header of an SDP packet."""

SCP_SVER_RECEIVE_LENGTH_MAX = 512
"""The smallest power of two large enough to handle that SVER will
produce (256 + 8 bytes).
"""

SPINNAKER_RTR_BASE = 0xE1000000  # Unbuffered
"""Base address of router hardware registers."""

SPINNAKER_RTR_P2P = SPINNAKER_RTR_BASE + 0x10000
"""Base address of P2P routing table."""

BMP_POWER_ON_TIMEOUT = 5.0
"""Additional timeout for BMP power-on commands to reply."""

# The following values are taken from BMPC.

BMP_ADC_MAX = 1 << 12
"""The range of values the BMP's 12-bit ADCs can measure."""

BMP_V_SCALE_2_5 = 2.5 / BMP_ADC_MAX
"""Multiplier to convert from ADC value to volts for lines less than 2.5 V."""

BMP_V_SCALE_3_3 = 3.75 / BMP_ADC_MAX
"""Multiplier to convert from ADC value to volts for 3.3 V lines."""
BMP_V_SCALE_12 = 15.0 / BMP_ADC_MAX
"""Multiplier to convert from ADC value to volts for 12 V lines."""

BMP_TEMP_SCALE = 1.0 / 256.0
"""Multiplier to convert from temperature probe values to degrees Celsius."""

BMP_MISSING_TEMP = -0x8000
"""Temperature value returned when a probe is not connected."""

BMP_MISSING_FAN = -1
"""Fan speed value returned when a fan is absent."""

RTR_ENTRIES = 1024
"""Number of routing table entries in each routing table.
"""

RTE_PACK_STRING = "<2H 3I"
"""Packing string used with routing table entries, values are (next, free,
route, key, mask).
"""


class SCPCommands(enum.IntEnum):
    """Command codes used in SCP packets."""
    sver = 0
    """Get the software version"""
    read = 2  # Read data
    write = 3  # Write data

    fill = 5  # Fill a number of words with a given value

    link_read = 17  # Send a NN (or FPGA reg) read command
    link_write = 18  # Send a NN (or FPGA reg) write command

    nearest_neighbour_packet = 20  # Send a nearest neighbour packet
    signal = 22  # Transmit a signal to applications
    flood_fill_data = 23  # Transmit flood-fill data

    led = 25  # Change the state of an LED
    iptag = 26  # Change/clear/get the value of an IPTag

    alloc_free = 28  # Allocate or free SDRAM and routing_table entries
    router = 29  # Router related commands

    info = 31  # Get info about a given chip (e.g. idle cores, dead links)

    bmp_info = 48  # Request various info structs from a BMP

    power = 57  # BMP main board power control


class SCPReturnCodes(enum.IntEnum):
    """SCP return codes"""
    ok = 0x80  # Command completed OK
    len = 0x81  # Bad packet length (Fatal)
    sum = 0x82  # Bad checksum (Retryable)
    cmd = 0x83  # Bad/invalid command (Fatal)
    arg = 0x84  # Invalid arguments (Fatal)
    port = 0x85  # Bad port number (Fatal)
    timeout = 0x86  # Monitor <-> app-core comms timeout (Fatal)
    route = 0x87  # No P2P route (Fatal)
    cpu = 0x88  # Bad CPU number (Fatal)
    dead = 0x89  # SHM dest dead (Fatal)
    buf = 0x8a  # No free SHM buffers (Fatal)
    p2p_noreply = 0x8b  # No reply to open (Fatal)
    p2p_reject = 0x8c  # Open rejected (Fatal)
    p2p_busy = 0x8d  # Dest busy (Retryable)
    p2p_timeout = 0x8e  # Eth chip <--> destination comms timeout (Fatal)
    pkt_tx = 0x8f  # Pkt Tx failed (Fatal)


RETRYABLE_SCP_RETURN_CODES = set([
    SCPReturnCodes.sum,
    SCPReturnCodes.p2p_busy,
])
"""The set of :py:class:`.SCPReturnCodes` values which indicate a non-fatal
retryable fault."""


FATAL_SCP_RETURN_CODES = {
    SCPReturnCodes.len: "Bad command length.",
    SCPReturnCodes.cmd: "Bad/invalid command.",
    SCPReturnCodes.arg: "Invalid command arguments.",
    SCPReturnCodes.port: "Bad port number.",
    SCPReturnCodes.timeout:
        "Timeout waiting for the application core to respond to "
        "the monitor core's request.",
    SCPReturnCodes.route: "No P2P route to the target chip is available.",
    SCPReturnCodes.cpu: "Bad CPU number.",
    SCPReturnCodes.dead: "SHM dest dead.",
    SCPReturnCodes.buf: "No free SHM buffers.",
    SCPReturnCodes.p2p_noreply:
        "No response packets from the target reached the "
        "ethernet connected chip.",
    SCPReturnCodes.p2p_reject: "The target chip rejected the packet.",
    SCPReturnCodes.p2p_timeout:
        "Communications between the ethernet connected chip and target chip "
        "timedout.",
    SCPReturnCodes.pkt_tx: "Packet transmission failed.",
}
"""The set of fatal SCP errors and a human-readable error."""


class DataType(enum.IntEnum):
    """Used to specify the size of data being read to/from a SpiNNaker machine
    over SCP.
    """
    byte = 0
    short = 1
    word = 2


class LEDAction(enum.IntEnum):
    """Indicate the action that should be applied to a given LED."""
    on = 3
    off = 2
    toggle = 1

    @classmethod
    def from_bool(cls, action):
        """Maps from a bool or None to toggle."""
        if action is None:
            return cls.toggle
        elif action:
            return cls.on
        else:
            return cls.off


class IPTagCommands(enum.IntEnum):
    """Indicate the action that should be performed to the given IPTag."""
    set = 1
    get = 2
    clear = 3


class AllocOperations(enum.IntEnum):
    """Used to allocate or free regions of SDRAM and routing table entries."""
    alloc_sdram = 0  # Allocate a region of SDRAM
    free_sdram_by_ptr = 1  # Free a region of SDRAM with a pointer
    free_sdram_by_tag = 2  # Free a region of SDRAM with a tag and app_id

    alloc_rtr = 3  # Allocate a region of routing table entries
    free_rtr_by_pos = 4  # Free routing table entries by index
    free_rtr_by_app = 5  # Free routing table entries by app_id


class RouterOperations(enum.IntEnum):
    """Operations that may be performed to the router."""
    init = 0
    clear = 1
    load = 2
    fixed_route_set_get = 3


class NNCommands(enum.IntEnum):
    """Nearest Neighbour operations."""
    flood_fill_start = 6
    flood_fill_core_select = 7
    flood_fill_end = 15


class NNConstants(enum.IntEnum):
    """Constants for use with nearest neighbour commands."""
    forward = 0x3f  # Forwarding configuration
    retry = 0x18  # Retry configuration


class AppFlags(enum.IntEnum):
    """Flags for application loading."""
    wait = 0x01


class AppState(enum.IntEnum):
    """States that an application may be in."""
    # Error states - further information may be available
    dead = 0
    power_down = 1
    runtime_exception = 2
    watchdog = 3

    # General states
    init = 4  # Transitory "(hopefully)"
    wait = 5  # Awaiting signal AppSignal.start (due to AppFlags.wait)
    c_main = 6  # Entered c_main
    run = 7  # Running application event loop
    pause = 10  # Paused by signal AppSignal.pause
    exit = 11  # Application returned from c_main
    idle = 15  # Prior to application loading

    # Awaiting synchronisation (at a barrier)
    sync0 = 8
    sync1 = 9


class RuntimeException(enum.IntEnum):
    """Runtime exceptions as reported by SARK."""
    none = 0  # No error
    reset = 1  # Branch through zero
    undefined_instruction = 2  # Undefined instruction
    svc = 3  # Undefined SVC or no handler
    prefetch_abort = 4  # Prefetch abort
    data_abort = 5  # Data abort
    unhandled_irq = 6  # Unhandled IRQ
    unhandled_fiq = 7  # Unhandled FIQ
    unconfigured_vic = 8  # Unconfigured VIC vector
    abort = 9  # Generic user abort
    malloc_failure = 10  # "malloc" failure
    division_by_zero = 11  # Divide by zero
    event_startup_failure = 12  # Event startup failure
    software_error = 13  # Fatal SW error
    iobuf_failure = 14  # Failed to allocate IO buffer
    bad_enable = 15  # Bad event enable
    null_pointer = 16  # Generic null pointer error
    pkt_startup_failure = 17  # Pkt startup failure
    timer_startup_failure = 18  # Timer startup failure
    api_startup_failure = 19  # API startup failure
    incompatible_version = 20  # SC&MP and API version mismatch


class AppSignal(enum.IntEnum):
    """Signals that may be transmitted to applications."""
    # General purpose signals
    init = 0  # (Re-)load default application (i.e. SARK)
    power_down = 1  # Power down cores.
    stop = 2  # Forcefully stop and cleanup an application
    start = 3  # Start applications in AppState.wait
    pause = 6  # Pause execution of an application
    cont = 7  # Continue execution after pausing
    exit = 8  # Request that an application terminate (drop to AppState.exit)
    timer = 9  # Manually trigger a timer interrupt

    # Barrier synchronisation
    sync0 = 4  # Continue from AppState.sync0
    sync1 = 5  # Continue from AppState.sync1

    # User defined signals
    usr0 = 10
    usr1 = 11
    usr2 = 12
    usr3 = 13


class AppDiagnosticSignal(enum.IntEnum):
    """Signals which interrogate the state of a machine.

    Note that a value is returned when any of these signals is sent.
    """
    OR = 0  # Is ANY core in a given state
    AND = 1  # Are ALL cores in a given state
    count = 2  # How many cores are in a state


class MessageType(enum.IntEnum):
    """Internally used to specify the type of a message."""
    multicast = 0
    peer_to_peer = 1
    nearest_neighbour = 2


signal_types = {
    AppSignal.init: MessageType.nearest_neighbour,
    AppSignal.power_down: MessageType.nearest_neighbour,
    AppSignal.start: MessageType.nearest_neighbour,
    AppSignal.stop: MessageType.nearest_neighbour,
    AppSignal.exit: MessageType.nearest_neighbour,

    AppSignal.sync0: MessageType.multicast,
    AppSignal.sync1: MessageType.multicast,
    AppSignal.pause: MessageType.multicast,
    AppSignal.cont: MessageType.multicast,
    AppSignal.timer: MessageType.multicast,
    AppSignal.usr0: MessageType.multicast,
    AppSignal.usr1: MessageType.multicast,
    AppSignal.usr2: MessageType.multicast,
    AppSignal.usr3: MessageType.multicast,
}
"""Mapping from an :py:class:`.AppSignal` to the :py:class:`.MessageType`
used to transmit it.
"""

diagnostic_signal_types = {
    AppDiagnosticSignal.AND: MessageType.peer_to_peer,
    AppDiagnosticSignal.OR: MessageType.peer_to_peer,
    AppDiagnosticSignal.count: MessageType.peer_to_peer,
}
"""Mapping from an :py:class:`.AppDiagnosticSignal` to the
:py:class:`.MessageType` used to transmit it.
"""


class P2PTableEntry(enum.IntEnum):
    """Routing table entry in the point-to-point SpiNNaker routing table."""
    east = 0b000
    north_east = 0b001
    north = 0b010
    west = 0b011
    south_west = 0b100
    south = 0b101
    none = 0b110  # No known route to this location
    monitor = 0b111  # Route to the monitor on this chip


class BMPInfoType(enum.IntEnum):
    """Type of information to return from a bmp_info SCP command."""
    serial = 0  # Board serial number
    can_status = 2  # Status of all CAN devices on the bus
    adc = 3  # ADC (e.g. voltage + temperature)
    ip_addr = 4  # IP Address


# Dictionary of (address % 4, n_bytes % 4) to data type
address_length_dtype = {
    (i, j): (DataType.word if (i == j == 0) else
             (DataType.short if (i % 2 == j % 2 == 0) else
              DataType.byte))
    for i in range(4) for j in range(4)
}

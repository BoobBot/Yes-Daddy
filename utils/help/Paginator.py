import discord


# code was given to me, edited for my needs
# seems to come from https://github.com/Rapptz/discord.py/blob/rewrite/discord/ext/commands/formatter.py#L56
class Paginator:

    def __init__(self, max_size=1000):
        self.max_size = max_size
        self._current_embed = discord.Embed()
        self._current_field = []
        self._count = 0
        self._embeds = []
        self.last_cog = None

    def add_line(self, line='', *, empty=False):

        if len(line) > self.max_size - 2:
            raise RuntimeError(f'Line exceeds maximum page size {self.max_size - 2}')

        if self._count + len(line) + 1 > self.max_size:
            self.close_page()

        self._count += len(line) + 1
        self._current_field.append(line)

        if empty:
            self._current_field.append('')

    def close_page(self):
        print(dir(self))
        name = value = ''
        while self._current_field:
            curr = self._current_field.pop(0)
            if curr.strip().endswith(':'):
                if name:
                    if value:
                        self._current_embed.add_field(name=name, value=value, inline=False)
                        name, value = curr, ''
                        self.last_cog = curr
                else:
                    if value:
                        if self.last_cog:
                            self._current_embed.add_field(
                                name=f'{self.last_cog} (continued)',
                                value=value,
                                inline=False)
                        value = ''
                    name = curr
                    self.last_cog = curr
            else:
                value += curr + '\n'

        if self.last_cog and value:
            self._current_embed.add_field(name=self.last_cog, value=value)
            value = ''

        if value and not self.last_cog:
            f = list(filter(None, value.split('\n')))
            y = "\n".join(f[1:])
            self._current_embed.description = f"\n{f[0]}\n{y}"

        self._embeds.append(self._current_embed)
        self._current_embed = discord.Embed()
        self._current_field = []
        self._count = 1

    @property
    def pages(self):
        if len(self._current_field) > 1:
            self.close_page()
        return self._embeds

    def __repr__(self):
        fmt = '<Paginator max_size: {0.max_size} count: {0._count}>'
        return fmt.format(self)
